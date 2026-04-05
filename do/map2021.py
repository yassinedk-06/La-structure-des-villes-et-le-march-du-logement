import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# ==========================================
# 1. CONFIGURATION DES CHEMINS
# ==========================================
CHEMIN_DO = os.path.dirname(os.path.abspath(__file__))
DOSSIER_PROJET = os.path.dirname(CHEMIN_DO)
DOSSIER_INPUT = os.path.join(DOSSIER_PROJET, 'input')
DOSSIER_OUTPUT = os.path.join(DOSSIER_PROJET, 'output')

# Recherche automatique du fichier Excel 2021
fichiers_input = os.listdir(DOSSIER_INPUT)
nom_excel_2021 = next((f for f in fichiers_input if '2021' in f and f.endswith('.xlsx')), None)
chemin_carte = os.path.join(DOSSIER_INPUT, 'COMMUNE.SHP')

if nom_excel_2021 is None:
    print("ERREUR : Fichier Excel 2021 introuvable dans le dossier input.")
    exit()

chemin_logement_2021 = os.path.join(DOSSIER_INPUT, nom_excel_2021)

# ==========================================
# 2. LECTURE DU FICHIER EXCEL (Onglet COM)
# ==========================================
print(f"Lecture brute du fichier {nom_excel_2021}...")

# header=None permet de tout lire sans chercher de titres
df_raw = pd.read_excel(chemin_logement_2021, sheet_name='COM', header=None, engine='openpyxl')

print("\n--- DIAGNOSTIC VISUEL ---")
# On affiche les 15 premieres lignes et les 5 premieres colonnes
print(df_raw.iloc[0:15, 0:5]) 
print("-------------------------\n")
exit()

# ==========================================
# 3. PIVOTAGE ET CALCUL
# ==========================================
print("Transformation des donnees...")
# On transforme les lignes de categories (1, 2, 3) en colonnes
df_2021 = df_raw.pivot_table(index='CODGEO', columns='CATL', values='NB', aggfunc='sum').reset_index()
df_2021 = df_2021.rename(columns={1: 'RP', 2: 'RS', 3: 'VAC'})

# Calcul du taux de vacance
df_2021['TOTAL'] = df_2021['RP'] + df_2021['RS'] + df_2021['VAC']
df_2021 = df_2021[df_2021['TOTAL'] > 0] # Eviter les divisions par zero
df_2021['taux_vacance_2021'] = (df_2021['VAC'] / df_2021['TOTAL']) * 100

# ==========================================
# 4. FUSION ET CORRECTION DES TROUS
# ==========================================
print("Fusion avec le fond de carte...")
carte = gpd.read_file(chemin_carte)

df_2021['CODGEO_STR'] = df_2021['CODGEO'].astype(str).str.zfill(5)
carte['INSEE_STR'] = carte['INSEE_COM'].astype(str).str.zfill(5)

# Fusion qui garde la forme de toutes les communes (how='left')
carte_finale = carte.merge(df_2021, left_on='INSEE_STR', right_on='CODGEO_STR', how='left')

# Remplissage des communes manquantes avec la moyenne nationale 2021
moyenne_nationale = carte_finale['taux_vacance_2021'].mean()
carte_finale['taux_vacance_rempli'] = carte_finale['taux_vacance_2021'].fillna(moyenne_nationale)

# ==========================================
# 5. DESSIN DE LA CARTE 2021
# ==========================================
print("Generation de la carte 2021...")
fig, ax = plt.subplots(1, 1, figsize=(12, 12))

# Fond gris de secours
carte.plot(ax=ax, color='#d9d9d9', edgecolor='none')

# Couche de donnees
carte_finale.plot(column='taux_vacance_rempli', 
                  ax=ax, 
                  cmap='OrRd', 
                  legend=True,
                  legend_kwds={'title': "Taux de vacance 2021 (%)", 'loc': 'lower left', 'fmt': "{:.1f}"},
                  scheme='NaturalBreaks', k=5)

ax.set_title("Evolution : Taux de vacance des logements par commune (2021)", fontsize=16)
ax.axis('off')

chemin_image = os.path.join(DOSSIER_OUTPUT, '03_carte_vacance_2021.png')
plt.savefig(chemin_image, dpi=300, bbox_inches='tight')

print(f"Termine ! Carte sauvegardee dans : {chemin_image}")
plt.show()