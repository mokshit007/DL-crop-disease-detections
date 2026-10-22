import os
import json
import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from src.model import get_model
from src.dataset import source_leaf_id

def _leaf_ids_in(split_dir):
    """Set of (class, source_leaf_id) pairs present in a split directory."""
    ids = set()
    for cls in os.listdir(split_dir):
        for name in os.listdir(os.path.join(split_dir, cls)):
            ids.add((cls, source_leaf_id(name)))
    return ids

def evaluate():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    os.makedirs('results', exist_ok=True)

    with open('class_names.json', 'r') as f:
        class_names = json.load(f)

    model = get_model(len(class_names), pretrained=False).to(device)
    model.load_state_dict(torch.load('models/best_model.pth', map_location=device, weights_only=True))
    model.eval()

    test_transforms = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    test_dataset = datasets.ImageFolder('data/processed/test', test_transforms)
    if test_dataset.classes != class_names:
        raise ValueError("Test folder classes do not match class_names.json")
    test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False, num_workers=4)

    all_preds = []
    all_labels = []

    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            _, preds = outputs.max(1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.numpy())
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)

    # Metrics
    acc = accuracy_score(all_labels, all_preds)
    macro_f1 = f1_score(all_labels, all_preds, average='macro')
    print(f"Test Accuracy: {acc*100:.2f}% | Macro F1: {macro_f1*100:.2f}% ({len(all_labels)} images)")

    # Leakage audit: test images whose source leaf (any rotated/flipped copy) also appears in train/val
    seen = _leaf_ids_in('data/processed/train') | _leaf_ids_in('data/processed/val')
    unseen_mask = np.array([
        (class_names[label], source_leaf_id(path)) not in seen
        for path, label in test_dataset.samples
    ])
    unseen_acc = accuracy_score(all_labels[unseen_mask], all_preds[unseen_mask]) if unseen_mask.any() else float('nan')
    print(f"Leaf-disjoint subset: {unseen_mask.sum()} / {len(unseen_mask)} test images "
          f"({100 * (1 - unseen_mask.mean()):.1f}% share a source leaf with train/val) -> Accuracy: {unseen_acc*100:.2f}%")

    report = classification_report(all_labels, all_preds, target_names=class_names, output_dict=True)
    with open('results/evaluation_report.json', 'w') as f:
        json.dump(report, f)

    with open('results/test_metrics.json', 'w') as f:
        json.dump({
            'test_images': int(len(all_labels)),
            'test_accuracy': round(acc * 100, 2),
            'test_macro_f1': round(macro_f1 * 100, 2),
            'leaked_fraction_pct': round(100 * (1 - unseen_mask.mean()), 1),
            'leaf_disjoint_images': int(unseen_mask.sum()),
            'leaf_disjoint_accuracy': round(unseen_acc * 100, 2)
        }, f, indent=4)

    # Confusion Matrix
    cm = confusion_matrix(all_labels, all_preds)
    plt.figure(figsize=(15, 12))
    sns.heatmap(cm, annot=False, cmap='Blues', xticklabels=class_names, yticklabels=class_names)
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    plt.savefig('results/confusion_matrix.png')
    plt.close()

    # Plot training curves if available
    if os.path.exists('results/metrics.json'):
        with open('results/metrics.json', 'r') as f:
            metrics = json.load(f)
        plt.figure(figsize=(12, 5))
        plt.subplot(1, 2, 1)
        plt.plot(metrics['train_losses'], label='Train Loss')
        plt.plot(metrics['val_losses'], label='Val Loss')
        plt.legend()
        plt.title('Loss')

        plt.subplot(1, 2, 2)
        plt.plot(metrics['train_accs'], label='Train Acc')
        plt.plot(metrics['val_accs'], label='Val Acc')
        plt.legend()
        plt.title('Accuracy')

        plt.tight_layout()
        plt.savefig('results/training_curves.png')
        plt.close()

if __name__ == '__main__':
    evaluate()
