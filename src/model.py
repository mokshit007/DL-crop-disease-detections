import torch
import torch.nn as nn
from torchvision.models import efficientnet_v2_s, EfficientNet_V2_S_Weights
from src.attention import CBAM, GeM

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

class EfficientNetV2_MSAF(nn.Module):
    """
    Proposed Architecture: EfficientNetV2-MSAF (Multi-Scale Attention Fusion)

    Drawbacks of the stock EfficientNetV2-S head that this addresses:
      1. Single-scale decision: only the final 7x7 map (1 cell = 32x32 px) reaches the classifier,
         so pin-point lesions (bacterial spot, Septoria specks, mite stippling) are averaged away.
         -> Taps three depths: stage 3 (64ch, 28x28), stage 5 (160ch, 14x14), head (1280ch, 7x7).
      2. No explicit lesion focus: background leaf tissue and studio backdrop weigh as much as
         lesions. -> A CBAM channel+spatial attention block on every tapped scale.
      3. Global average pooling dilutes small, strongly-activated regions.
         -> Learnable GeM pooling per scale.
      4. Fine-detail features are the first to break under blur / sensor noise.
         -> Fusing coarse and fine scales lets the classifier fall back on coarse evidence,
            and scale-dropout during training stops it relying on any single scale.
    """
    TAPS = (3, 5, 7)  # indices into base.features
    TAP_CHANNELS = (64, 160, 1280)

    def __init__(self, num_classes=38, pretrained=True, scale_dropout=0.1):
        super().__init__()
        weights = EfficientNet_V2_S_Weights.DEFAULT if pretrained else None
        base = efficientnet_v2_s(weights=weights)
        self.features = base.features
        self.scale_dropout = scale_dropout

        self.attn = nn.ModuleList([CBAM(in_channels=c, reduction_ratio=16, kernel_size=7) for c in self.TAP_CHANNELS])
        self.pools = nn.ModuleList([GeM() for _ in self.TAP_CHANNELS])
        # Normalise each scale's descriptor so the 64/160-dim fine scales are not drowned out by the 1280-dim head
        self.norms = nn.ModuleList([nn.LayerNorm(c) for c in self.TAP_CHANNELS])

        fused = sum(self.TAP_CHANNELS)
        self.classifier = nn.Sequential(
            nn.Dropout(p=0.3, inplace=True),
            nn.Linear(fused, num_classes)
        )

    def forward(self, x):
        descriptors = []
        tap = 0
        for i, block in enumerate(self.features):
            x = block(x)
            if i == self.TAPS[tap]:
                f = self.attn[tap](x)
                d = self.norms[tap](torch.flatten(self.pools[tap](f), 1))
                descriptors.append(d)
                tap += 1
                if tap == len(self.TAPS):
                    break
        if self.training and self.scale_dropout > 0:
            # Drop whole scales per sample (never all of them) to force redundancy across scales
            keep = (torch.rand(x.size(0), len(descriptors), device=x.device) > self.scale_dropout).float()
            keep[keep.sum(1) == 0, -1] = 1.0
            descriptors = [d * keep[:, j:j + 1] for j, d in enumerate(descriptors)]
        return self.classifier(torch.cat(descriptors, dim=1))

ARCHITECTURES = ('baseline', 'cbam', 'msaf')

def get_model(num_classes, use_cbam=False, pretrained=True, arch=None):
    """Factory: arch in {'baseline', 'cbam', 'msaf'} (use_cbam=True is kept as an alias for 'cbam').
    Pass pretrained=False when a trained checkpoint will be loaded (skips the ImageNet download)."""
    arch = arch or ('cbam' if use_cbam else 'baseline')
    if arch == 'msaf':
        return EfficientNetV2_MSAF(num_classes=num_classes, pretrained=pretrained)
    if arch == 'cbam':
        return EfficientNetV2_CBAM(num_classes=num_classes, pretrained=pretrained)
        
    weights = EfficientNet_V2_S_Weights.DEFAULT if pretrained else None
    model = efficientnet_v2_s(weights=weights)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model

if __name__ == '__main__':
    for arch in ARCHITECTURES:
        model = get_model(38, pretrained=False, arch=arch)
        total_params = sum(p.numel() for p in model.parameters())
        out = model.eval()(torch.randn(2, 3, 224, 224))
        print(f"{arch:9s} {model.__class__.__name__:22s} params={total_params:,} out={tuple(out.shape)}")
