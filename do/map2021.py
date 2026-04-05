import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# ==========================================
# 1. CONFIGURATION DES CHEMINS (Architecture portable)
# ==========================================
# On utilise la librairie 'os' pour rendre le script indépendant de l'ordinateur.
# Au lieu de coder un chemin absolu ("C:/..."), on crée des chemins relatifs.
CHEMIN_DO = os.path.dirname(os.path.abspath(__file__)) # Dossier du script actuel
DOSSIER_PROJET = os.path.dirname(CHEMIN_DO)            # Racine du projet
DOSSIER_INPUT = os.path.join(DOSSIER_PROJET, 'input')  # Dossier des données brutes
DOSSIER_OUTPUT = os.path.join(DOSSIER_PROJET, 'output')# Dossier des résultats

# Recherche dynamique du fichier 2021 : le script scanne le dossier 
# et prend automatiquement le fichier Excel contenant '2021'.
fichiers_input = os.listdir(DOSSIER_INPUT)
nom_excel_2021 = next((f for f in fichiers_input if '2021' in f and f.endswith('.xlsx')), None)
nom_carte = "COMMUNE.SHP" 

chemin_logement_2021 = os.path.join(DOSSIER_INPUT, nom_excel_2021)
chemin_carte = os.path.join(DOSSIER_INPUT, nom_carte)

# ==========================================
# 2. CHARGEMENT ET NETTOYAGE (Data Engineering)
# ==========================================
print("Chargement des donnees Insee 2021...")
# skiprows=10 permet d'ignorer le long cartouche de présentation de l'Insee
df_raw = pd.read_excel(chemin_logement_2021, sheet_name='COM', skiprows=10, engine='openpyxl')

# PROTECTION DU CODE INSEE (Clé primaire)
# On cherche dynamiquement la colonne qui contient 'CODGEO'
col_codgeo = next((c for c in df_raw.columns if 'CODGEO' in str(c)), 'CODGEO')

# Nettoyage par Expression Régulière (Regex) : 
# 1. On transforme en texte (.astype(str))
# 2. On supprime les ".0" invisibles à la fin (.replace)
# 3. On enlève les espaces cachés (.strip)
# 4. On force à 5 caractères avec des zéros à gauche (.zfill)
df_raw[col_codgeo] = df_raw[col_codgeo].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.zfill(5)

print("Calcul des totaux avec CATL4...")
# UTILISATION DE LISTES EN COMPRÉHENSION (List Comprehension)
# On scanne les noms de colonnes et on "aspire" toutes celles qui nous intéressent.
colonnes_vacantes = [col for col in df_raw.columns if 'CATL4' in str(col)] # Que les vacants
colonnes_totales = [col for col in df_raw.columns if 'CATL' in str(col)]   # Tous les types de logements

# SÉCURISATION DES TYPES (Casting)
# On force la conversion en nombres. 'coerce' transforme le texte parasite en NaN, 
# et 'fillna(0)' remplace ces NaN par des zéros pour pouvoir faire des additions.
df_vac_num = df_raw[colonnes_vacantes].apply(pd.to_numeric, errors='coerce').fillna(0)
df_tot_num = df_raw[colonnes_totales].apply(pd.to_numeric, errors='coerce').fillna(0)

# INITIALISATION DU DATAFRAME PROPRE
df_2021 = pd.DataFrame()
df_2021['CODGEO_STR'] = df_raw[col_codgeo]

# AGGRÉGATION : .sum(axis=1) additionne les colonnes horizontalement (ligne par ligne)
df_2021['VAC'] = df_vac_num.sum(axis=1)
df_2021['TOTAL'] = df_tot_num.sum(axis=1)

# ÉLIMINATION DES ABERRATIONS : On supprime les villes à 0 logement pour éviter de diviser par zéro
df_2021 = df_2021[df_2021['TOTAL'] > 0].copy()

# CALCUL FINAL DE LA VARIABLE CIBLE
df_2021['taux_vacance'] = (df_2021['VAC'] / df_2021['TOTAL']) * 100

# ==========================================
# 3. CHARGEMENT DE LA CARTE ET FUSION (Spatio-Data)
# ==========================================
print("Chargement de la carte et fusion...")
carte = gpd.read_file(chemin_carte)

# On applique le même blindage (Regex + zfill) sur les codes de la carte 
# pour que la clé de jointure soit parfaite des deux côtés.
carte['INSEE_STR'] = carte['INSEE_COM'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.zfill(5)

# FUSION (Merge) en "Left Join"
# On garde tous les polygones géographiques, et on vient y coller les données 2021
carte_finale = carte.merge(df_2021, left_on='INSEE_STR', right_on='CODGEO_STR', how='left')

# DIAGNOSTIC : On compte combien de villes ont été matchées avec succès.
nb_match = carte_finale['taux_vacance'].notna().sum()
print(f"\nSUCCESS ! Nombre de communes fusionnees : {nb_match}\n")

# ==========================================
# 4. DESSIN DE LA CARTE (Data Viz)
# ==========================================
print("Generation de la carte thermique...")

fig, ax = plt.subplots(1, 1, figsize=(12, 10))

# COUCHE 1 : Fond de carte (Secours)
# Dessine la carte de base en gris. edgecolor='none' efface les frontières.
carte.plot(ax=ax, color='#d9d9d9', edgecolor='none')

# COUCHE 2 : Données statistiques
carte_finale.plot(column='taux_vacance', 
                  ax=ax, 
                  cmap='OrRd', # Palette Orange/Rouge
                  legend=True,
                  scheme='UserDefined', 
                  classification_kwds={'bins': [5, 7, 9, 12]}, # Paliers définis manuellement
                  legend_kwds={'title': "Taux de vacance 2021 (%)", 'loc': 'lower left'},
                  # missing_kwds : Les communes "nouvelles" non trouvées seront transparentes ('none')
                  # laissant apparaître le gris de la couche du dessous.
                  missing_kwds={'color': 'none'},
                  # LA GOMME : Supprime les frontières noires pour éviter l'effet "tache d'encre"
                  edgecolor='none') 

ax.set_title("Taux de vacance des logements par commune (2021)", fontsize=15)
ax.axis('off') # On supprime le cadre autour du dessin

# EXPORT DE L'IMAGE (Pour le rapport)
chemin_image = os.path.join(DOSSIER_OUTPUT, '03_carte_vacance_2021.png')
plt.savefig(chemin_image, dpi=300, bbox_inches='tight')
print(f"Termine ! La carte coloree est dans : {chemin_image}")

# EXPORT DES DONNÉES (Pour l'algorithme d'étalement urbain)
# On sauvegarde le DataFrame propre en CSV pour qu'il soit lu par le script 'analyse.py'.
chemin_export = os.path.join(DOSSIER_OUTPUT, 'donnees_vacance_2021_propres.csv')
df_2021.to_csv(chemin_export, index=False, sep=';')
print(f"Données sauvegardées pour l'étape finale dans : {chemin_export}")

plt.show()