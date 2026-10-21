import os
import json
import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from src.model import get_model

def evaluate():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    with open('class_names.json', 'r') as f:
        class_names = json.load(f)
        
    model = get_model(len(class_names)).to(device)
    model.load_state_dict(torch.load('models/best_model.pth', map_location=device))
    model.eval()
    
    test_transforms = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    test_dataset = datasets.ImageFolder('data/processed/test', test_transforms)
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
            
    # Metrics
    acc = accuracy_score(all_labels, all_preds)
    print(f"Test Accuracy: {acc*100:.2f}%")
    
    report = classification_report(all_labels, all_preds, target_names=class_names, output_dict=True)
    with open('results/evaluation_report.json', 'w') as f:
        json.dump(report, f)
        
    # Confusion Matrix
    cm = confusion_matrix(all_labels, all_preds)
    plt.figure(figsize=(15, 12))
    sns.heatmap(cm, annot=False, cmap='Blues', xticklabels=class_names, yticklabels=class_names)
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    plt.savefig('results/confusion_matrix.png')
    
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

if __name__ == '__main__':
    evaluate()
