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
nom_excel_2012 = next((f for f in fichiers_input if '2012' in f and f.lower().endswith('.xls')), None)
nom_carte = "COMMUNE.SHP" 

chemin_logement_2012 = os.path.join(DOSSIER_INPUT, nom_excel_2012)
chemin_carte = os.path.join(DOSSIER_INPUT, nom_carte)

# ==========================================
# 2. CHARGEMENT ET NETTOYAGE (Donnees)
# ==========================================
print("Chargement des donnees Insee...")
df_2012 = pd.read_excel(chemin_logement_2012, sheet_name='COM_2012', skiprows=4)

col_vacants = 'Logements vacants en 2012 (princ)'
col_totaux = 'Logements en 2012 (princ)'
df_2012[col_vacants] = pd.to_numeric(df_2012[col_vacants], errors='coerce')
df_2012[col_totaux] = pd.to_numeric(df_2012[col_totaux], errors='coerce')

# On evite les divisions par zero
df_2012 = df_2012[df_2012[col_totaux] > 0].copy()

# Calcul du taux de vacance
df_2012['taux_vacance'] = (df_2012[col_vacants] / df_2012[col_totaux]) * 100

# ==========================================
# 3. CHARGEMENT DE LA CARTE ET FUSION
# ==========================================
print("Chargement de la carte et fusion...")
carte = gpd.read_file(chemin_carte)

# Harmonisation des codes Insee (5 chiffres)
df_2012['CODGEO_STR'] = df_2012['Code géographique'].astype(str).str.zfill(5)
carte['INSEE_STR'] = carte['INSEE_COM'].astype(str).str.zfill(5)

# La fusion (how='left' pour garder toutes les frontieres)
carte_finale = carte.merge(df_2012, left_on='INSEE_STR', right_on='CODGEO_STR', how='left')

# Remplissage des trous avec la moyenne de 2012
moyenne_nationale = carte_finale['taux_vacance'].mean()
carte_finale['taux_vacance_rempli'] = carte_finale['taux_vacance'].fillna(moyenne_nationale)

# ==========================================
# 4. DESSIN DE LA CARTE
# ==========================================
print("Generation de la carte thermique...")

fig, ax = plt.subplots(1, 1, figsize=(12, 10))

# Fond gris de secours
carte.plot(ax=ax, color='#d9d9d9', edgecolor='none')

# Couche de donnees avec tes paliers personnalises
carte_finale.plot(column='taux_vacance_rempli', 
                  ax=ax, 
                  cmap='OrRd', 
                  legend=True,
                  scheme='UserDefined', 
                  classification_kwds={'bins': [4, 6, 8, 10]}, # Tes propres seuils !
                  legend_kwds={'title': "Taux de vacance 2012 (%)", 'loc': 'lower left'})

ax.set_title("Taux de vacance des logements par commune (2012)", fontsize=15)
ax.axis('off')

# Sauvegarde
chemin_image = os.path.join(DOSSIER_OUTPUT, '02_carte_vacance_2012.png')
plt.savefig(chemin_image, dpi=300, bbox_inches='tight')

print(f"Termine ! La carte coloree est dans : {chemin_image}")
plt.show()