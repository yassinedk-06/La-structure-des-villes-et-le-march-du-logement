import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# ==========================================
# 1. CONFIGURATION DES CHEMINS (Architecture Robuste)
# ==========================================
# On utilise la librairie 'os' pour créer des chemins relatifs.
# Cela garantit que le code fonctionnera sur n'importe quel ordinateur 
# (Windows, Mac) sans avoir à écrire le chemin en dur (ex: C:/Users/...).

# CHEMIN_DO trouve le dossier actuel du script.
CHEMIN_DO = os.path.dirname(os.path.abspath(__file__))
# On remonte d'un cran pour trouver la racine du projet.
DOSSIER_PROJET = os.path.dirname(CHEMIN_DO)
# On définit automatiquement les dossiers d'entrée et de sortie.
DOSSIER_INPUT = os.path.join(DOSSIER_PROJET, 'input')
DOSSIER_OUTPUT = os.path.join(DOSSIER_PROJET, 'output')

# Recherche automatique du fichier Excel 2012 dans le dossier input
fichiers_input = os.listdir(DOSSIER_INPUT)
nom_excel_2012 = next((f for f in fichiers_input if '2012' in f and f.lower().endswith('.xls')), None)
nom_carte = "COMMUNE.SHP" 

# Création des chemins finaux pour la lecture
chemin_logement_2012 = os.path.join(DOSSIER_INPUT, nom_excel_2012)
chemin_carte = os.path.join(DOSSIER_INPUT, nom_carte)

# ==========================================
# 2. CHARGEMENT ET NETTOYAGE (Data Preparation)
# ==========================================
print("Chargement des donnees Insee...")
# On lit l'onglet 'COM_2012'. skiprows=4 permet de sauter les en-têtes inutiles de l'Insee.
df_2012 = pd.read_excel(chemin_logement_2012, sheet_name='COM_2012', skiprows=4)

col_vacants = 'Logements vacants en 2012 (princ)'
col_totaux = 'Logements en 2012 (princ)'

# SÉCURISATION : pd.to_numeric force la conversion en nombres mathématiques.
# errors='coerce' transforme le texte parasite (mis par erreur par l'Insee) en vide (NaN)
# au lieu de faire crasher le script.
df_2012[col_vacants] = pd.to_numeric(df_2012[col_vacants], errors='coerce')
df_2012[col_totaux] = pd.to_numeric(df_2012[col_totaux], errors='coerce')

# NETTOYAGE : On supprime les communes ayant 0 logement total.
# Cela empêche l'algorithme de faire une division par zéro (qui déclencherait un crash).
df_2012 = df_2012[df_2012[col_totaux] > 0].copy()

# CRÉATION DE VARIABLE : Formule du Taux de Vacance
df_2012['taux_vacance'] = (df_2012[col_vacants] / df_2012[col_totaux]) * 100

# ==========================================
# 3. CHARGEMENT DE LA CARTE ET FUSION (Jointure Spatiale)
# ==========================================
print("Chargement de la carte et fusion...")
# geopandas (gpd) lit le shapefile (les polygones géographiques de la France)
carte = gpd.read_file(chemin_carte)

# NORMALISATION : On s'assure que les codes Insee sont du texte (str)
# et on utilise .zfill(5) pour ajouter un zéro devant les codes à 4 chiffres (ex: 1001 -> 01001).
# Cela permet de fusionner correctement des départements comme l'Ain ou la Corse.
df_2012['CODGEO_STR'] = df_2012['Code géographique'].astype(str).str.zfill(5)
carte['INSEE_STR'] = carte['INSEE_COM'].astype(str).str.zfill(5)

# FUSION (Merge) : On colle les données Excel sur les polygones de la carte.
# how='left' signifie : "On garde toutes les communes de la carte, même celles 
# qui n'ont pas trouvé de correspondance dans le fichier Excel."
carte_finale = carte.merge(df_2012, left_on='INSEE_STR', right_on='CODGEO_STR', how='left')

# IMPUTATION : Pour les communes sans données (ex: communes ayant fusionné),
# on calcule la moyenne nationale et on remplit les "trous" (fillna) avec cette valeur.
moyenne_nationale = carte_finale['taux_vacance'].mean()
carte_finale['taux_vacance_rempli'] = carte_finale['taux_vacance'].fillna(moyenne_nationale)

# ==========================================
# 4. DESSIN DE LA CARTE (Data Visualization)
# ==========================================
print("Generation de la carte thermique...")

# Création d'une toile de 12 par 10 pouces
fig, ax = plt.subplots(1, 1, figsize=(12, 10))

# COUCHE 1 : Fond de carte global
# On dessine toutes les communes en gris. edgecolor='none' supprime les bordures noires
# pour éviter que la carte ne soit qu'une énorme tache d'encre à l'échelle nationale.
carte.plot(ax=ax, color='#d9d9d9', edgecolor='none')

# COUCHE 2 : Carte Choroplèthe (La donnée)
# On superpose les couleurs en fonction de la colonne 'taux_vacance_rempli'
carte_finale.plot(column='taux_vacance_rempli', 
                  ax=ax, 
                  cmap='OrRd', # Palette Orange/Rouge (Orange-Red)
                  legend=True,
                  scheme='UserDefined', # On n'utilise pas l'échelle automatique...
                  classification_kwds={'bins': [5, 7, 9, 12]}, # ... on impose nos propres paliers analytiques !
                  legend_kwds={'title': "Taux de vacance 2012 (%)", 'loc': 'lower left'})

# Titre et nettoyage visuel (on enlève le cadre autour de la carte)
ax.set_title("Taux de vacance des logements par commune (2012)", fontsize=15)
ax.axis('off')

# EXPORTATION : Sauvegarde en Haute Définition (300 dpi) pour les rapports
# bbox_inches='tight' recadre l'image pour supprimer les marges blanches inutiles
chemin_image = os.path.join(DOSSIER_OUTPUT, '02_carte_vacance_2012.png')
plt.savefig(chemin_image, dpi=300, bbox_inches='tight')

print(f"Termine ! La carte coloree est dans : {chemin_image}")
plt.show()