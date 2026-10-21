import torch
import torch.nn as nn
from torchvision.models import efficientnet_v2_s, EfficientNet_V2_S_Weights
from src.attention import CBAM

class EfficientNetV2_CBAM(nn.Module):
    """
    Proposed Architecture: EfficientNetV2-CBAM
    Augments the Fused-MBConv feature representations with a dual Channel & Spatial Attention Module (CBAM)
    prior to global average pooling to pinpoint subtle micro-lesions and necrotic margins.
    """
    def __init__(self, num_classes=38, pretrained=True):
        super().__init__()
        weights = EfficientNet_V2_S_Weights.DEFAULT if pretrained else None
        base = efficientnet_v2_s(weights=weights)
        self.features = base.features
        
        # Dual-Attention Module on 1280 feature channels
        self.cbam = CBAM(in_channels=1280, reduction_ratio=16, kernel_size=7)
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        
        in_features = base.classifier[1].in_features
        self.classifier = nn.Sequential(
            nn.Dropout(p=0.2, inplace=True),
            nn.Linear(in_features, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.cbam(x)  # Channel & Spatial recalibration
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x

def get_model(num_classes, use_cbam=False):
    """Factory function returning standard EfficientNetV2-S or Proposed EfficientNetV2-CBAM."""
    if use_cbam:
        return EfficientNetV2_CBAM(num_classes=num_classes, pretrained=True)
        
    weights = EfficientNet_V2_S_Weights.DEFAULT
    model = efficientnet_v2_s(weights=weights)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model

if __name__ == '__main__':
    model = get_model(38, use_cbam=True)
    print("Novel Proposed Model initialized:", model.__class__.__name__)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total Parameters with CBAM: {total_params:,}")
