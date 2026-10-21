import torch
import torch.nn as nn
from torchvision.models import efficientnet_v2_s, EfficientNet_V2_S_Weights

def get_model(num_classes):
    # Using State-of-the-Art EfficientNetV2-S
    # It has excellent parameter efficiency, faster training, and higher accuracy than older models like ResNet or standard EfficientNet.
    weights = EfficientNet_V2_S_Weights.DEFAULT
    model = efficientnet_v2_s(weights=weights)
    
    # Replace the final classification head
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    
    return model

if __name__ == '__main__':
    model = get_model(38)
    print("SOTA Model initialized:", model.__class__.__name__)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total Parameters: {total_params:,}")
