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

fichiers_input = os.listdir(DOSSIER_INPUT)
nom_excel_2021 = next((f for f in fichiers_input if '2021' in f and f.endswith('.xlsx')), None)
nom_carte = "COMMUNE.SHP" 

chemin_logement_2021 = os.path.join(DOSSIER_INPUT, nom_excel_2021)
chemin_carte = os.path.join(DOSSIER_INPUT, nom_carte)

# ==========================================
# 2. CHARGEMENT ET NETTOYAGE (Donnees)
# ==========================================
print("Chargement des donnees Insee 2021...")
df_raw = pd.read_excel(chemin_logement_2021, sheet_name='COM', skiprows=10, engine='openpyxl')

# Protection et nettoyage des codes communes
col_codgeo = next((c for c in df_raw.columns if 'CODGEO' in str(c)), 'CODGEO')
df_raw[col_codgeo] = df_raw[col_codgeo].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.zfill(5)

print("Calcul des totaux avec CATL4...")
# 1. Isolation des colonnes
colonnes_vacantes = [col for col in df_raw.columns if 'CATL4' in str(col)]
colonnes_totales = [col for col in df_raw.columns if 'CATL' in str(col)]

# 2. Conversion en nombres
df_vac_num = df_raw[colonnes_vacantes].apply(pd.to_numeric, errors='coerce').fillna(0)
df_tot_num = df_raw[colonnes_totales].apply(pd.to_numeric, errors='coerce').fillna(0)

# 3. Initialisation du dataframe 2021
df_2021 = pd.DataFrame()
df_2021['CODGEO_STR'] = df_raw[col_codgeo]
df_2021['VAC'] = df_vac_num.sum(axis=1)
df_2021['TOTAL'] = df_tot_num.sum(axis=1)

# On evite les divisions par zero
df_2021 = df_2021[df_2021['TOTAL'] > 0].copy()

# Calcul du taux de vacance
df_2021['taux_vacance'] = (df_2021['VAC'] / df_2021['TOTAL']) * 100

# ==========================================
# 3. CHARGEMENT DE LA CARTE ET FUSION
# ==========================================
print("Chargement de la carte et fusion...")
carte = gpd.read_file(chemin_carte)

# Harmonisation des codes Insee (5 chiffres) et protection
carte['INSEE_STR'] = carte['INSEE_COM'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.zfill(5)

# La fusion (how='left' pour garder toutes les frontieres)
carte_finale = carte.merge(df_2021, left_on='INSEE_STR', right_on='CODGEO_STR', how='left')

# DIAGNOSTIC
nb_match = carte_finale['taux_vacance'].notna().sum()
print(f"\nSUCCESS ! Nombre de communes fusionnees : {nb_match}\n")

# ==========================================
# 4. DESSIN DE LA CARTE
# ==========================================
print("Generation de la carte thermique...")

fig, ax = plt.subplots(1, 1, figsize=(12, 10))

# Fond gris de secours
carte.plot(ax=ax, color='#d9d9d9', edgecolor='none')

# Couche de donnees avec tes paliers personnalises
# Couche de donnees
carte_finale.plot(column='taux_vacance', # (ou 'taux_vacance' pour 2012)
                  ax=ax, 
                  cmap='OrRd', 
                  legend=True,
                  scheme='UserDefined', 
                  classification_kwds={'bins': [5, 7, 9, 12]}, # Tes propres seuils !
                  legend_kwds={'title': "Taux de vacance 2021 (%)", 'loc': 'lower left'},
                  missing_kwds={'color': 'none'},
                  edgecolor='none') # <--- LA SOLUTION EST ICI ! LE COUP DE GOMME !

ax.set_title("Taux de vacance des logements par commune (2021)", fontsize=15)
ax.axis('off')

# Sauvegarde
chemin_image = os.path.join(DOSSIER_OUTPUT, '03_carte_vacance_2021.png')
plt.savefig(chemin_image, dpi=300, bbox_inches='tight')

print(f"Termine ! La carte coloree est dans : {chemin_image}")
plt.show()