import os
import shutil
import random
from pathlib import Path
from tqdm import tqdm
import kagglehub

def prepare_dataset(dest_dir, split_ratios=(0.8, 0.1, 0.1), seed=42):
    random.seed(seed)
    
    print("Downloading the comprehensive 38-class dataset via kagglehub...")
    # This dataset contains 38 classes and ~87K images
    path = kagglehub.dataset_download('vipoooool/new-plant-diseases-dataset')
    
    print(f"Dataset downloaded to: {path}")
    
    # Locate the directories containing the actual class folders
    # Usually it's in a folder like 'New Plant Diseases Dataset(Augmented)/New Plant Diseases Dataset(Augmented)/train'
    base_raw_dirs = []
    for root, dirs, files in os.walk(path):
        # Identify directory containing plant classes
        if any(d.lower().startswith('apple___') or d.lower().startswith('tomato___') for d in dirs):
            base_raw_dirs.append(root)
            
    if not base_raw_dirs:
        raise FileNotFoundError("Could not find the dataset images folder inside the downloaded kagglehub dataset.")

    # We will gather images from all found directories (train/valid splits inside the zip)
    # and re-split them ourselves to ensure consistency.
    
    dest_path = Path(dest_dir)
    train_dir = dest_path / 'train'
    val_dir = dest_path / 'val'
    test_dir = dest_path / 'test'
    
    for d in [train_dir, val_dir, test_dir]:
        d.mkdir(parents=True, exist_ok=True)
        
    # Gather all images across all matching base directories
    all_classes = set()
    for base_dir in base_raw_dirs:
        for d in Path(base_dir).iterdir():
            if d.is_dir():
                all_classes.add(d.name)
                
    print(f"Found {len(all_classes)} distinct classes.")
    
    # Dictionary to hold all image paths per class
    class_images = {cls: [] for cls in all_classes}
    
    print("Gathering image paths...")
    for base_dir in base_raw_dirs:
        for cls in all_classes:
            cls_path = Path(base_dir) / cls
            if cls_path.exists():
                images = list(cls_path.glob('*.jpg')) + list(cls_path.glob('*.JPG')) + list(cls_path.glob('*.png'))
                class_images[cls].extend(images)
                
    for cls in tqdm(all_classes, desc="Processing and Splitting classes"):
        (train_dir / cls).mkdir(exist_ok=True)
        (val_dir / cls).mkdir(exist_ok=True)
        (test_dir / cls).mkdir(exist_ok=True)
        
        images = class_images[cls]
        # Remove duplicates if any (by filename/path)
        images = list(set(images))
        images = sorted(images)
        random.shuffle(images)
        
        n_total = len(images)
        n_train = int(n_total * split_ratios[0])
        n_val = int(n_total * split_ratios[1])
        
        train_imgs = images[:n_train]
        val_imgs = images[n_train:n_train+n_val]
        test_imgs = images[n_train+n_val:]
        
        for img in train_imgs:
            shutil.copy2(img, train_dir / cls / img.name)
        for img in val_imgs:
            shutil.copy2(img, val_dir / cls / img.name)
        for img in test_imgs:
            shutil.copy2(img, test_dir / cls / img.name)
            
    print("Dataset preparation complete! Extracted to:", dest_dir)

if __name__ == '__main__':
    dest = 'data/processed'
    if not os.path.exists(os.path.join(dest, 'train')):
        prepare_dataset(dest)
    else:
        print("Dataset already processed.")
