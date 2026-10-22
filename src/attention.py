import torch
import torch.nn as nn
import torch.nn.functional as F

class ChannelAttention(nn.Module):
    """
    Channel Attention Module: Squeezes spatial dimensions via both Average and Max Pooling,
    then processes them through a shared Multi-Layer Perceptron (MLP) to determine
    which feature channels carry disease-specific pathological information.
    """
    def __init__(self, in_channels, reduction_ratio=16):
        super(ChannelAttention, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        
        reduced_channels = max(8, in_channels // reduction_ratio)
        self.mlp = nn.Sequential(
            nn.Linear(in_channels, reduced_channels, bias=False),
            nn.SiLU(inplace=True),
            nn.Linear(reduced_channels, in_channels, bias=False)
        )
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        b, c, _, _ = x.size()
        avg_out = self.mlp(self.avg_pool(x).view(b, c))
        max_out = self.mlp(self.max_pool(x).view(b, c))
        channel_weights = self.sigmoid(avg_out + max_out).view(b, c, 1, 1)
        return x * channel_weights


class SpatialAttention(nn.Module):
    """
    Spatial Attention Module: Aggregates channel information across each pixel via Max and Average Pooling,
    followed by a large 7x7 convolution to pinpoint the exact 2D spatial coordinates of leaf lesions.
    """
    def __init__(self, kernel_size=7):
        super(SpatialAttention, self).__init__()
        assert kernel_size in (3, 7), "Kernel size must be 3 or 7"
        padding = 3 if kernel_size == 7 else 1
        self.conv = nn.Conv2d(2, 1, kernel_size=kernel_size, padding=padding, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        avg_out = torch.mean(x, dim=1, keepdim=True)
        max_out, _ = torch.max(x, dim=1, keepdim=True)
        combined = torch.cat([avg_out, max_out], dim=1)
        spatial_weights = self.sigmoid(self.conv(combined))
        return x * spatial_weights


class CBAM(nn.Module):
    """
    Convolutional Block Attention Module (CBAM):
    Sequential combination of Channel Attention and Spatial Attention with a residual connection:
        F'  = Mc(F) * F
        F'' = Ms(F') * F'
        Out = F + F''
    """
    def __init__(self, in_channels, reduction_ratio=16, kernel_size=7):
        super(CBAM, self).__init__()
        self.channel_attention = ChannelAttention(in_channels, reduction_ratio)
        self.spatial_attention = SpatialAttention(kernel_size)

    def forward(self, x):
        residual = x
        out = self.channel_attention(x)
        out = self.spatial_attention(out)
        return residual + out


class GeM(nn.Module):
    """
    Generalized-Mean Pooling with a learnable exponent p:
        GeM(F) = ( mean(F^p) )^(1/p)
    p = 1 is average pooling, p -> inf approaches max pooling. Learning p lets the network
    emphasise small, strongly-activated lesion regions that plain average pooling dilutes.
    """
    def __init__(self, p=3.0, eps=1e-6):
        super(GeM, self).__init__()
        self.p = nn.Parameter(torch.ones(1) * p)
        self.eps = eps

    def forward(self, x):
        p = self.p.clamp(min=1.0)
        return F.adaptive_avg_pool2d(x.float().clamp(min=self.eps).pow(p), 1).pow(1.0 / p).to(x.dtype)
