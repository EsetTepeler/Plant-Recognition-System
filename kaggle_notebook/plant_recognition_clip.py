# =============================================================
# 🌿 PLANT RECOGNITION - CLIP ZERO-SHOT (Kaggle Compatible)
# =============================================================
# Bu versiyon Kaggle ortamında çalışacak şekilde optimize edildi
# sentence-transformers kullanarak daha stabil CLIP yükleme
# =============================================================

# STEP 1: Install stable packages
!pip install -q sentence-transformers pillow

import os
import gradio as gr
import torch
from PIL import Image
import numpy as np

print("✅ Libraries loaded")

# =============================================================
# Device Setup
# =============================================================
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🖥️ Device: {device}")

# =============================================================
# CLIP Model Loading (with sentence-transformers - more stable)
# =============================================================
print("📦 Loading CLIP model...")

from sentence_transformers import SentenceTransformer

# This model is more stable in Kaggle environment
clip_model = SentenceTransformer('clip-ViT-B-32')
clip_model = clip_model.to(device)
print("✅ CLIP model loaded")

# =============================================================
# PlantCLEF Species - Load from Dataset
# =============================================================
DATASET_PATH = "/kaggle/input/plantclef2025"

def load_species():
    """Load species from PlantCLEF dataset folders"""
    species = set()
    
    if os.path.exists(DATASET_PATH):
        print(f"📂 Scanning: {DATASET_PATH}")
        for root, dirs, files in os.walk(DATASET_PATH):
            for d in dirs:
                if not d.startswith('.') and not d.startswith('_'):
                    name = d.replace('_', ' ').strip()
                    if len(name) >= 3:
                        species.add(name)
        print(f"✅ Found {len(species)} species from dataset")
    
    return sorted(list(species))

species_list = load_species()

# Fallback species if dataset not available
if len(species_list) < 100:
    print("⚠️ Using fallback species list...")
    species_list = sorted(list(set(species_list + [
        "Rosa gallica", "Rosa damascena", "Rosa canina",
        "Tulipa gesneriana", "Helianthus annuus", "Lavandula angustifolia",
        "Cosmos atrosanguineus", "Cosmos bipinnatus", "Dahlia pinnata",
        "Chrysanthemum morifolium", "Narcissus pseudonarcissus",
        "Lilium candidum", "Orchis mascula", "Phalaenopsis amabilis",
        "Anthurium andraeanum", "Hibiscus rosa-sinensis",
        "Jasminum officinale", "Magnolia grandiflora", "Camellia japonica",
        "Paeonia lactiflora", "Hydrangea macrophylla", "Wisteria sinensis",
        "Bougainvillea spectabilis", "Plumeria rubra", "Aloe vera",
        "Quercus robur", "Pinus sylvestris", "Acer platanoides",
        "Betula pendula", "Fagus sylvatica", "Tilia cordata",
        "Fraxinus excelsior", "Populus tremula", "Salix alba",
        "Cedrus libani", "Picea abies", "Ginkgo biloba",
        "Eucalyptus globulus", "Olea europaea", "Ficus carica",
        "Prunus avium", "Malus domestica", "Citrus sinensis",
        "Solanum lycopersicum", "Capsicum annuum", "Cucumis sativus",
        "Lactuca sativa", "Brassica oleracea", "Daucus carota",
        "Mentha piperita", "Ocimum basilicum", "Rosmarinus officinalis",
        "Thymus vulgaris", "Salvia officinalis", "Origanum vulgare",
        "Echeveria elegans", "Crassula ovata", "Opuntia ficus-indica",
        "Monstera deliciosa", "Ficus benjamina", "Dracaena marginata",
        "Philodendron scandens", "Spathiphyllum wallisii",
        "Taraxacum officinale", "Trifolium pratense", "Papaver rhoeas",
        "Centaurea cyanus", "Matricaria chamomilla", "Achillea millefolium",
        "Viola odorata", "Primula vulgaris", "Ranunculus acris"
    ])))

print(f"🌿 Total species: {len(species_list)}")

# =============================================================
# Pre-compute text embeddings for species (once)
# =============================================================
print("📊 Computing species embeddings...")

# Create descriptive prompts for better matching
species_prompts = [f"a photograph of {sp}, a plant species" for sp in species_list]
species_embeddings = clip_model.encode(species_prompts, convert_to_tensor=True, device=device)
species_embeddings = species_embeddings / species_embeddings.norm(dim=-1, keepdim=True)

print(f"✅ Pre-computed embeddings for {len(species_list)} species")

# =============================================================
# Plant Identification Function
# =============================================================
def identify_plant(image, top_k=5):
    """Identify plant using CLIP zero-shot classification"""
    if image is None:
        return {"Error: No image": 1.0}
    
    try:
        # Convert to PIL
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        image = image.convert("RGB")
        
        # Get image embedding
        image_embedding = clip_model.encode(image, convert_to_tensor=True, device=device)
        image_embedding = image_embedding / image_embedding.norm()
        
        # Compute similarities
        similarities = (image_embedding @ species_embeddings.T).cpu().numpy()
        
        # Softmax to get probabilities
        exp_sim = np.exp(similarities * 10)  # Temperature scaling
        probs = exp_sim / exp_sim.sum()
        
        # Top-k results
        top_idx = probs.argsort()[::-1][:top_k]
        
        results = {}
        for idx in top_idx:
            results[species_list[idx]] = float(probs[idx])
            print(f"  → {species_list[idx]}: {probs[idx]:.2%}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {f"Error: {str(e)}": 1.0}

# =============================================================
# Gradio Interface
# =============================================================
demo = gr.Interface(
    fn=identify_plant,
    inputs=gr.Image(label="🌿 Upload Plant Image"),
    outputs=gr.Label(num_top_classes=5, label="🔍 Identified Plants"),
    title="🌿 PlantCLEF Recognition AI",
    description=f"CLIP Zero-Shot | {len(species_list)} species",
)

print("\n🚀 Starting server...")
demo.launch(share=True)
