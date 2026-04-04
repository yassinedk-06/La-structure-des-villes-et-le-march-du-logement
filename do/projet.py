import os
import geopandas as gpd
import matplotlib.pyplot as plt

# ==========================================
# 1. CONFIGURATION DES CHEMINS
# ==========================================
CHEMIN_DO = os.path.dirname(os.path.abspath(__file__))
DOSSIER_PROJET = os.path.dirname(CHEMIN_DO)

DOSSIER_INPUT = os.path.join(DOSSIER_PROJET, 'input')
DOSSIER_OUTPUT = os.path.join(DOSSIER_PROJET, 'output')

# Le chemin est maintenant super simple !
chemin_carte = os.path.join(DOSSIER_INPUT, 'COMMUNE.SHP')

# ==========================================
# 2. CHARGEMENT ET VÉRIFICATION
# ==========================================
print("⏳ Chargement du fond de carte (cela prend quelques secondes)...")
carte_communes = gpd.read_file(chemin_carte)
print(f"✅ Succès ! La carte contient {len(carte_communes)} communes.")

# ==========================================
# 3. DESSIN DE LA CARTE
# ==========================================
print("🎨 Génération du dessin...")

fig, ax = plt.subplots(1, 1, figsize=(10, 10))
carte_communes.plot(ax=ax, color='#e8e8e8', edgecolor='white', linewidth=0.1)

ax.axis('off')
ax.set_title("Fond de carte des Communes (Prêt pour l'analyse)", fontsize=16)

# Sauvegarde dans le dossier output
chemin_sauvegarde = os.path.join(DOSSIER_OUTPUT, '01_carte_communes.png')
plt.savefig(chemin_sauvegarde, dpi=300, bbox_inches='tight')

print(f"🚀 Terminé ! Image sauvegardée dans : {chemin_sauvegarde}")

# Afficher à l'écran
plt.show()