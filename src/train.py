import os
import json
import time
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from tqdm import tqdm

from src.model import get_model, ARCHITECTURES
from src.splits import load_split, ManifestDataset, OneCopyPerLeafSampler

IMAGENET_MEAN, IMAGENET_STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]

class AddGaussianNoise:
    """Simulates low-light smartphone sensor noise on a [0, 1] tensor."""
    def __init__(self, max_std=0.1):
        self.max_std = max_std

    def __call__(self, t):
        return (t + torch.randn_like(t) * torch.rand(1).item() * self.max_std).clamp(0, 1)

def build_transforms(field_aug=False):
    train_tf = [
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
    ]
    if field_aug:
        # Field-condition augmentation: defocus/shake blur and sensor noise (applied to 30% / 30%)
        train_tf.append(transforms.RandomApply([transforms.GaussianBlur(9, sigma=(0.5, 3.0))], p=0.3))
    train_tf.append(transforms.ToTensor())
    if field_aug:
        train_tf.append(transforms.RandomApply([AddGaussianNoise(0.12)], p=0.3))
    train_tf.append(transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD))

    val_tf = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)
    ])
    return transforms.Compose(train_tf), val_tf

def run_name(arch, field_aug):
    return f"{arch}_field" if field_aug else arch

def train(arch='baseline', split='leaf', epochs=10, batch_size=32, learning_rate=1e-3, field_aug=False, seed=42, num_workers=3):
    torch.manual_seed(seed)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    use_amp = device.type == 'cuda'
    name = run_name(arch, field_aug)
    print(f"Training '{name}' on device: {device}")
    os.makedirs('models', exist_ok=True)
    os.makedirs('results', exist_ok=True)

    data_dir = 'data/processed'
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"Processed data directory not found: {data_dir}. Run src/dataset.py first.")

    train_transforms, val_transforms = build_transforms(field_aug)

    # Load Datasets. 'leaf' = leaf-disjoint manifest (no augmented copy of a leaf in two splits);
    # 'folders' = the original data/processed/{train,val} folders.
    if split == 'leaf':
        manifest = load_split()
        class_names = manifest['class_names']
        train_dataset = ManifestDataset(manifest['train'], train_transforms)
        val_dataset = ManifestDataset(manifest['val'], val_transforms)
        train_sampler = OneCopyPerLeafSampler(manifest['train'], seed=seed)
    else:
        train_dataset = datasets.ImageFolder(os.path.join(data_dir, 'train'), train_transforms)
        val_dataset = datasets.ImageFolder(os.path.join(data_dir, 'val'), val_transforms)
        class_names = train_dataset.classes
        train_sampler = None
    with open('class_names.json', 'w') as f:
        json.dump(class_names, f)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=train_sampler is None,
                              sampler=train_sampler, num_workers=num_workers,
                              pin_memory=True, persistent_workers=True, drop_last=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers,
                            pin_memory=True, persistent_workers=True)

    # Model Setup
    model = get_model(len(class_names), arch=arch).to(device)

    # Label Smoothing improves generalization for large datasets
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

    # AdamW is generally better than Adam for models with weight decay
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)

    # OneCycleLR is SOTA for fast convergence
    scheduler = optim.lr_scheduler.OneCycleLR(
        optimizer, max_lr=learning_rate,
        steps_per_epoch=len(train_loader),
        epochs=epochs
    )

    # AMP Scaler for mixed precision (FP16 autocast + loss scaling only on CUDA)
    scaler = torch.amp.GradScaler('cuda', enabled=use_amp)

    best_val_acc = 0.0
    history = {'run': name, 'arch': arch, 'split': split, 'train_images_per_epoch': len(train_loader) * batch_size, 'field_aug': field_aug, 'epochs': epochs,
               'batch_size': batch_size, 'lr': learning_rate, 'seed': seed,
               'train_losses': [], 'val_losses': [], 'train_accs': [], 'val_accs': [], 'epoch_seconds': []}
    ckpt_path = f'models/{name}.pth'
    resume_path = f'models/{name}_last.pt'
    start_epoch = 0

    # Resume from the end of the last completed epoch (training state is saved every epoch)
    if os.path.exists(resume_path):
        state = torch.load(resume_path, map_location=device, weights_only=False)
        model.load_state_dict(state['model'])
        optimizer.load_state_dict(state['optimizer'])
        scheduler.load_state_dict(state['scheduler'])
        scaler.load_state_dict(state['scaler'])
        if train_sampler is not None and state.get('sampler_rng') is not None:
            train_sampler.generator.set_state(state['sampler_rng'].cpu())
        torch.set_rng_state(state['torch_rng'].cpu())
        history, best_val_acc, start_epoch = state['history'], state['best_val_acc'], state['epoch'] + 1
        print(f"Resuming '{name}' from epoch {start_epoch + 1} (best val acc so far {best_val_acc:.2f}%)")

    print(f"Starting training for {epochs} epochs with {len(class_names)} classes "
          f"({len(train_loader) * batch_size} train samples per epoch / {len(val_dataset)} val images)...")

    for epoch in range(start_epoch, epochs):
        t0 = time.time()
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        # Training loop with AMP
        train_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs} [Train]", mininterval=30)
        for inputs, labels in train_bar:
            inputs, labels = inputs.to(device, non_blocking=True), labels.to(device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)

            with torch.amp.autocast('cuda', enabled=use_amp):
                outputs = model(inputs)
                loss = criterion(outputs, labels)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()

            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

            train_bar.set_postfix({'loss': f'{loss.item():.4f}'}, refresh=False)

        train_loss = running_loss / len(train_loader)
        train_acc = 100. * correct / total

        # Validation loop
        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device, non_blocking=True), labels.to(device, non_blocking=True)

                with torch.amp.autocast('cuda', enabled=use_amp):
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)

                val_loss += loss.item()
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()

        val_loss = val_loss / len(val_loader)
        val_acc = 100. * correct / total

        print(f"Epoch {epoch+1} - Train Loss: {train_loss:.4f} Acc: {train_acc:.2f}% | "
              f"Val Loss: {val_loss:.4f} Acc: {val_acc:.2f}% | {time.time() - t0:.0f}s", flush=True)

        history['train_losses'].append(train_loss)
        history['val_losses'].append(val_loss)
        history['train_accs'].append(train_acc)
        history['val_accs'].append(val_acc)
        history['epoch_seconds'].append(round(time.time() - t0, 1))

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), ckpt_path)
            print(f"Best model saved -> {ckpt_path}")

        # Save metrics every epoch so an interrupted run still leaves a history
        history['best_val_acc'] = best_val_acc
        with open(f'results/history_{name}.json', 'w') as f:
            json.dump(history, f, indent=2)
        torch.save({
            'model': model.state_dict(), 'optimizer': optimizer.state_dict(),
            'scheduler': scheduler.state_dict(), 'scaler': scaler.state_dict(),
            'sampler_rng': train_sampler.generator.get_state() if train_sampler is not None else None,
            'torch_rng': torch.get_rng_state(),
            'history': history, 'best_val_acc': best_val_acc, 'epoch': epoch,
        }, resume_path)

    # Training finished: the resume state is no longer needed
    if os.path.exists(resume_path):
        os.remove(resume_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--arch', choices=ARCHITECTURES, default='baseline')
    parser.add_argument('--split', choices=('leaf', 'folders'), default='leaf')
    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--batch-size', type=int, default=32)  # 32 fits a 4 GB GPU with AMP
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--field-aug', action='store_true', help='Add blur / sensor-noise training augmentation')
    parser.add_argument('--workers', type=int, default=3)
    args = parser.parse_args()
    train(arch=args.arch, split=args.split, epochs=args.epochs, batch_size=args.batch_size,
          learning_rate=args.lr, field_aug=args.field_aug, num_workers=args.workers)
