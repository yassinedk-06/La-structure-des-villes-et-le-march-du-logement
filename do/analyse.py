import os
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 1. CONFIGURATION DES CHEMINS (Architecture relative)
# ==========================================
# Définition dynamique des répertoires pour garantir la portabilité du code
CHEMIN_DO = os.path.dirname(os.path.abspath(__file__))
DOSSIER_PROJET = os.path.dirname(CHEMIN_DO)
DOSSIER_INPUT = os.path.join(DOSSIER_PROJET, 'input')
DOSSIER_OUTPUT = os.path.join(DOSSIER_PROJET, 'output')

# Fichiers cibles : On récupère l'export propre de notre précédent script (2021) 
# et la base de données brute du Cerema sur l'étalement urbain.
fichier_vacance = os.path.join(DOSSIER_OUTPUT, 'donnees_vacance_2021_propres.csv')
fichier_conso = os.path.join(DOSSIER_INPUT, 'conso2009_2024_resultats_com.csv')

# ==========================================
# 2. LECTURE DES DONNEES (Data Ingestion)
# ==========================================
print("Chargement des donnees de vacance...")
# On force le code Insee en texte (str) dès la lecture pour éviter de perdre les zéros initiaux
df_vac = pd.read_csv(fichier_vacance, sep=';', dtype={'CODGEO_STR': str})

print("Chargement des donnees d'etalement urbain (Cerema)...")
# low_memory=False : Empêche Pandas de planter si une colonne mélange du texte et des nombres.
# .copy() : Optimisation mémoire pour éviter la fragmentation du DataFrame.
df_conso = pd.read_csv(fichier_conso, sep=';', dtype={'idcom': str}, low_memory=False).copy()

# ==========================================
# 3. FUSION ET CORRECTION DES UNITES (Data Cleaning & Merge)
# ==========================================
print("Fusion des deux bases de donnees...")
# Normalisation de la clé de jointure (Code Insee) à 5 caractères
df_conso['idcom_str'] = df_conso['idcom'].str.strip().str.zfill(5)

# JOINTURE INTERNE (Inner Join) : 
# On ne conserve STRICTEMENT que les communes qui existent à la fois dans le fichier Insee ET le fichier Cerema.
df_final = pd.merge(df_vac, df_conso, left_on='CODGEO_STR', right_on='idcom_str', how='inner')

# NETTOYAGE TYPOGRAPHIQUE (Le Bug de la virgule)
# Les données de l'État français utilisent des virgules pour les décimales.
# Python (américain) exige des points. On fait donc un "Chercher/Remplacer" massif.
df_final['taux_vacance'] = df_final['taux_vacance'].astype(str).str.replace(',', '.')
df_final['art09hab24'] = df_final['art09hab24'].astype(str).str.replace(',', '.')

# CASTING (Conversion de types)
# Maintenant que le texte est propre, on force la conversion en valeurs numériques réelles (float).
df_final['taux_vacance'] = pd.to_numeric(df_final['taux_vacance'], errors='coerce')
df_final['art09hab24'] = pd.to_numeric(df_final['art09hab24'], errors='coerce')

# ÉLIMINATION DES VALEURS MANQUANTES (Drop NaNs)
df_final = df_final.dropna(subset=['taux_vacance', 'art09hab24'])

# CONVERSION D'UNITÉ (Le point clé de la lisibilité)
# Le Cerema fournit la donnée en mètres carrés (m2). 
# Pour un affichage graphique compréhensible, on divise par 10 000 pour passer en Hectares.
df_final['art09hab24'] = df_final['art09hab24'] / 10000

# ==========================================
# 4. ANALYSE STATISTIQUE (Machine Learning basique)
# ==========================================
# Calcul du coefficient de corrélation linéaire de Pearson
# Il mesure l'intensité de la relation entre nos deux variables (de -1 à 1).
correlation = df_final['taux_vacance'].corr(df_final['art09hab24'])
print(f"\n---> Coefficient de correlation de Pearson : {correlation:.3f}")

# Algorithme d'interprétation textuelle dans le terminal
if correlation > 0:
    print("INTERPRETATION : Plus la vacance est elevee, plus la ville s'etale (Paradoxe absolu !)")
else:
    print("INTERPRETATION : Plus la vacance est elevee, moins la ville s'etale (Comportement logique).")
print("")

# ==========================================
# 5. DESSIN DU GRAPHIQUE NUAGE DE POINTS (Data Visualization)
# ==========================================
print("Generation du nuage de points...")
fig, ax = plt.subplots(figsize=(12, 8))

# TRACÉ DU NUAGE (Scatter Plot)
# alpha=0.3 : On rend les points transparents à 70%. C'est une technique cruciale 
# pour gérer "l'overplotting" (quand 35 000 points se superposent, la transparence crée un effet de densité).
ax.scatter(df_final['taux_vacance'], df_final['art09hab24'], alpha=0.3, color='#2980b9', s=15, edgecolors='none')

# Habillage du graphique (Titres et labels)
ax.set_title("Taux de vacance vs Étalement urbain pour l'habitat (2009-2024)", fontsize=16, pad=15)
ax.set_xlabel("Taux de vacance des logements en 2021 (%)", fontsize=12)
ax.set_ylabel("Nouvelle artificialisation pour l'habitat (Hectares)", fontsize=12)

# RECADRAGE DES AXES (Gestion des Outliers/Valeurs extrêmes)
# On limite volontairement le champ de vision pour exclure visuellement les quelques mégalopoles 
# (qui écraseraient l'échelle) et se concentrer sur la masse des communes françaises.
ax.set_xlim(0, 30)  # Taux de vacance de 0 à 30%
ax.set_ylim(0, 150) # Étalement de 0 à 150 Hectares

# Ajout d'une grille discrète pour faciliter la lecture des coordonnées
ax.grid(True, linestyle='--', alpha=0.7)

# EXPORT DE L'IMAGE
chemin_image = os.path.join(DOSSIER_OUTPUT, '04_graphique_vacance_etalement.png')
plt.savefig(chemin_image, dpi=300, bbox_inches='tight')

print(f"Termine ! Le graphique est sauvegarde dans : {chemin_image}")
plt.show()