import os
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 1. CONFIGURATION DES CHEMINS
# ==========================================
CHEMIN_DO = os.path.dirname(os.path.abspath(__file__))
DOSSIER_PROJET = os.path.dirname(CHEMIN_DO)
DOSSIER_INPUT = os.path.join(DOSSIER_PROJET, 'input')
DOSSIER_OUTPUT = os.path.join(DOSSIER_PROJET, 'output')

fichier_vacance = os.path.join(DOSSIER_OUTPUT, 'donnees_vacance_2021_propres.csv')
fichier_conso = os.path.join(DOSSIER_INPUT, 'conso2009_2024_resultats_com.csv')

# ==========================================
# 2. LECTURE DES DONNEES (Warnings corrigés)
# ==========================================
print("Chargement des donnees de vacance...")
df_vac = pd.read_csv(fichier_vacance, sep=';', dtype={'CODGEO_STR': str})

print("Chargement des donnees d'etalement urbain (Cerema)...")
df_conso = pd.read_csv(fichier_conso, sep=';', dtype={'idcom': str}, low_memory=False).copy()

# ==========================================
# 3. FUSION ET CORRECTION DES UNITES
# ==========================================
print("Fusion des deux bases de donnees...")
df_conso['idcom_str'] = df_conso['idcom'].str.strip().str.zfill(5)

df_final = pd.merge(df_vac, df_conso, left_on='CODGEO_STR', right_on='idcom_str', how='inner')

# Traducteur Francais -> Americain
df_final['taux_vacance'] = df_final['taux_vacance'].astype(str).str.replace(',', '.')
df_final['art09hab24'] = df_final['art09hab24'].astype(str).str.replace(',', '.')

df_final['taux_vacance'] = pd.to_numeric(df_final['taux_vacance'], errors='coerce')
df_final['art09hab24'] = pd.to_numeric(df_final['art09hab24'], errors='coerce')

df_final = df_final.dropna(subset=['taux_vacance', 'art09hab24'])

# ---> LA SOLUTION EST ICI : Conversion des m2 en Hectares <---
df_final['art09hab24'] = df_final['art09hab24'] / 10000

# ==========================================
# 4. ANALYSE STATISTIQUE
# ==========================================
correlation = df_final['taux_vacance'].corr(df_final['art09hab24'])
print(f"\n---> Coefficient de correlation de Pearson : {correlation:.3f}")

if correlation > 0:
    print("INTERPRETATION : Plus la vacance est elevee, plus la ville s'etale (Paradoxe absolu !)")
else:
    print("INTERPRETATION : Plus la vacance est elevee, moins la ville s'etale (Comportement logique).")
print("")

# ==========================================
# 5. DESSIN DU GRAPHIQUE NUAGE DE POINTS 
# ==========================================
print("Generation du nuage de points...")
fig, ax = plt.subplots(figsize=(12, 8))

ax.scatter(df_final['taux_vacance'], df_final['art09hab24'], alpha=0.3, color='#2980b9', s=15, edgecolors='none')

ax.set_title("Taux de vacance vs Étalement urbain pour l'habitat (2009-2024)", fontsize=16, pad=15)
ax.set_xlabel("Taux de vacance des logements en 2021 (%)", fontsize=12)
ax.set_ylabel("Nouvelle artificialisation pour l'habitat (Hectares)", fontsize=12)

# On garde notre belle echelle 10x10, mais cette fois les donnees vont rentrer dedans !
ax.set_xlim(0, 30)


ax.set_ylim(0, 150)


ax.grid(True, linestyle='--', alpha=0.7)

chemin_image = os.path.join(DOSSIER_OUTPUT, '04_graphique_vacance_etalement.png')
plt.savefig(chemin_image, dpi=300, bbox_inches='tight')

print(f"Termine ! Le graphique est sauvegarde dans : {chemin_image}")
plt.show()