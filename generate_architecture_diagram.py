"""
Generate Plant Recognition System Architecture Diagram
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.lines as mlines

# Set up the figure with dark background
fig, ax = plt.subplots(figsize=(16, 12))
fig.patch.set_facecolor("#0f172a")
ax.set_facecolor("#0f172a")
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis("off")

# Color palette
BLUE = "#3b82f6"
CYAN = "#06b6d4"
PURPLE = "#a855f7"
GREEN = "#10b981"
ORANGE = "#f97316"
RED = "#ef4444"
LIGHT_BG = "#1e293b"


def create_box(ax, x, y, width, height, text, color, alpha=0.8):
    """Create a glassmorphic box with text"""
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.05",
        edgecolor=color,
        facecolor=LIGHT_BG,
        alpha=alpha,
        linewidth=2,
    )
    ax.add_patch(box)
    ax.text(
        x + width / 2,
        y + height / 2,
        text,
        ha="center",
        va="center",
        color="white",
        fontsize=9,
        fontweight="bold",
        wrap=True,
    )
    return box


def create_arrow(ax, x1, y1, x2, y2, color=CYAN):
    """Create a glowing arrow"""
    arrow = FancyArrowPatch(
        (x1, y1),
        (x2, y2),
        arrowstyle="->",
        mutation_scale=20,
        color=color,
        linewidth=2.5,
        alpha=0.8,
        linestyle="-",
    )
    ax.add_patch(arrow)
    return arrow


# Title
ax.text(
    5,
    9.5,
    "Plant Recognition System Architecture",
    ha="center",
    va="center",
    color="white",
    fontsize=20,
    fontweight="bold",
)

# ============ TOP LAYER: USER INTERFACE ============
ax.text(
    5,
    8.8,
    "USER INTERFACE LAYER",
    ha="center",
    color=CYAN,
    fontsize=12,
    fontweight="bold",
)
create_box(ax, 1, 8.2, 3, 0.4, "React.js 18 + Material-UI", BLUE)
create_box(ax, 4.5, 8.2, 2, 0.4, "Image Upload", BLUE)
create_box(ax, 7, 8.2, 2, 0.4, "Chat Interface", BLUE)

create_arrow(ax, 5, 8.2, 5, 7.8)

# ============ SECURITY LAYER ============
ax.text(
    5,
    7.6,
    "SECURITY PIPELINE",
    ha="center",
    color=ORANGE,
    fontsize=12,
    fontweight="bold",
)
security_items = [
    "API Key Auth",
    "Rate Limiting",
    "Size Check (≤10MB)",
    "MIME Verify",
    "Magic Bytes",
    "PIL Sanitize",
]
for i, item in enumerate(security_items):
    create_box(ax, 0.5 + i * 1.5, 7, 1.3, 0.3, item, ORANGE, alpha=0.7)

create_arrow(ax, 5, 7, 5, 6.5)

# ============ API LAYER ============
ax.text(
    5, 6.3, "API ENDPOINTS", ha="center", color=PURPLE, fontsize=12, fontweight="bold"
)
create_box(ax, 1.5, 5.7, 1.5, 0.4, "/health", PURPLE)
create_box(ax, 3.2, 5.7, 1.5, 0.4, "/recognize", PURPLE)
create_box(ax, 4.9, 5.7, 2, 0.4, "/chat-with-image", PURPLE)
create_box(ax, 7.2, 5.7, 1.5, 0.4, "/status", PURPLE)

create_arrow(ax, 5, 5.7, 5, 5.3)

# ============ SERVICE LAYER ============
ax.text(
    5, 5.1, "SERVICE LAYER", ha="center", color=GREEN, fontsize=12, fontweight="bold"
)

# CLIP Service with preprocessing
create_box(ax, 0.3, 3.8, 1.8, 0.5, "CLIP Service\n(ViT-B/32)", GREEN)
create_box(ax, 0.3, 3.2, 0.85, 0.4, "Median\nFilter", CYAN, alpha=0.6)
create_box(ax, 1.25, 3.2, 0.85, 0.4, "Sharpen\n+Contrast", CYAN, alpha=0.6)
create_box(ax, 0.3, 2.7, 1.8, 0.3, "TTA (5 crops)", CYAN, alpha=0.6)

# External Services
create_box(ax, 2.5, 3.8, 1.6, 0.5, "Kaggle PlantCLEF\n(1.5TB Dataset)", GREEN)
create_box(ax, 4.3, 3.8, 1.5, 0.5, "PlantNet API", GREEN)
create_box(ax, 6, 3.8, 1.6, 0.5, "USDA Service\n(93K Plants)", GREEN)
create_box(ax, 7.8, 3.8, 1.8, 0.5, "LLM Service\n(Gemini/OpenRouter)", GREEN)

# Database Services
create_box(ax, 0.5, 2.2, 1.8, 0.4, "Weaviate\n(Vector DB)", GREEN)
create_box(ax, 2.5, 2.2, 1.5, 0.4, "Redis Cache", GREEN)
create_box(ax, 4.2, 2.2, 1.6, 0.4, "PostgreSQL", GREEN)

create_arrow(ax, 5, 2.2, 5, 1.8)

# ============ DATA LAYER ============
ax.text(
    5,
    1.6,
    "DATA STORAGE LAYER",
    ha="center",
    color=BLUE,
    fontsize=12,
    fontweight="bold",
)
create_box(ax, 1.5, 0.8, 2, 0.6, "PostgreSQL\n(Metadata)", BLUE)
create_box(ax, 4, 0.8, 2, 0.6, "Weaviate Cloud\n(Vectors)", BLUE)
create_box(ax, 6.5, 0.8, 2, 0.6, "External APIs\n(PlantNet, Google)", BLUE)

# Process flow annotations
ax.text(
    9.5,
    8,
    "①",
    ha="center",
    color=CYAN,
    fontsize=16,
    fontweight="bold",
    bbox=dict(boxstyle="circle", facecolor=LIGHT_BG, edgecolor=CYAN),
)
ax.text(
    9.5,
    7,
    "②",
    ha="center",
    color=ORANGE,
    fontsize=16,
    fontweight="bold",
    bbox=dict(boxstyle="circle", facecolor=LIGHT_BG, edgecolor=ORANGE),
)
ax.text(
    9.5,
    5.7,
    "③",
    ha="center",
    color=PURPLE,
    fontsize=16,
    fontweight="bold",
    bbox=dict(boxstyle="circle", facecolor=LIGHT_BG, edgecolor=PURPLE),
)
ax.text(
    9.5,
    3.8,
    "④",
    ha="center",
    color=GREEN,
    fontsize=16,
    fontweight="bold",
    bbox=dict(boxstyle="circle", facecolor=LIGHT_BG, edgecolor=GREEN),
)
ax.text(
    9.5,
    1.1,
    "⑤",
    ha="center",
    color=BLUE,
    fontsize=16,
    fontweight="bold",
    bbox=dict(boxstyle="circle", facecolor=LIGHT_BG, edgecolor=BLUE),
)

# Footer
ax.text(
    5,
    0.3,
    "Plant Recognition System | FastAPI + React | CLIP + Vector DB + LLM",
    ha="center",
    color="#64748b",
    fontsize=10,
    style="italic",
)

plt.tight_layout()

# Save the diagram
output_path = "plant_recognition_architecture.png"
plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="#0f172a")
print(f"✅ Architecture diagram saved to: {output_path}")
plt.close()
