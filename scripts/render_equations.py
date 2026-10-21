import os
import matplotlib.pyplot as plt

os.makedirs('results', exist_ok=True)

plt.rcParams['font.family'] = 'serif'
plt.rcParams['mathtext.fontset'] = 'cm'

equations = [
    (
        "results/eq_channel_attention.png",
        r"$\mathbf{M}_c(\mathbf{F}) = \sigma\left(\mathrm{MLP}(\mathrm{AvgPool}(\mathbf{F})) + \mathrm{MLP}(\mathrm{MaxPool}(\mathbf{F}))\right)$",
        (7.5, 1.2),
        '#1E40AF' # Deep Blue
    ),
    (
        "results/eq_spatial_attention.png",
        r"$\mathbf{M}_s(\mathbf{F}) = \sigma\left(f^{7\times 7}\left(\left[\mathrm{AvgPool}(\mathbf{F}); \, \mathrm{MaxPool}(\mathbf{F})\right]\right)\right)$",
        (7.2, 1.2),
        '#047857' # Deep Green
    ),
    (
        "results/eq_cbam_fusion.png",
        r"$\mathbf{F}' = \mathbf{M}_c(\mathbf{F}) \otimes \mathbf{F}, \quad \mathbf{F}'' = \mathbf{M}_s(\mathbf{F}') \otimes \mathbf{F}', \quad \mathbf{Y} = \mathbf{F} + \mathbf{F}''$",
        (8.5, 1.2),
        '#6D28D9' # Purple
    ),
    (
        "results/eq_severity_index.png",
        r"$\mathrm{Severity \,\, Index} \,\, (\mathcal{S}) = \frac{\int \int_{\Omega_{\mathrm{leaf}}} I(\mathrm{CAM}(x, y) \geq \tau) \, dx dy}{\int \int_{\Omega_{\mathrm{leaf}}} 1 \, dx dy} \times 100\%$",
        (8.2, 1.3),
        '#B45309' # Amber
    ),
    (
        "results/eq_label_smoothing.png",
        r"$y_k^{\mathrm{smooth}} = (1 - \epsilon) \, y_k + \frac{\epsilon}{K}, \quad \text{where } \epsilon = 0.1, \; K = 38$",
        (7.0, 1.1),
        '#334155' # Slate
    )
]

for filename, latex_str, size, text_color in equations:
    fig, ax = plt.subplots(figsize=size, dpi=300)
    ax.text(0.5, 0.5, latex_str, fontsize=17, ha='center', va='center', color=text_color)
    ax.axis('off')
    plt.savefig(filename, bbox_inches='tight', transparent=True, pad_inches=0.08)
    plt.close()
    print(f"Rendered: {filename}")

print("All mathematical equations rendered to crisp 300-DPI images successfully!")
