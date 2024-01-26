# -*- coding: utf-8 -*-
"""
Created on Sat Dec 16 15:18:45 2023

@author: lstei
"""


### ------------------------    Imports    ------------------------ ###
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import geopandas as gpd
import psycopg2
import ast
from sqlalchemy import create_engine



### ------------------------    Fonctions    ------------------------ ###

class Point:
    """
    Représente un point dans un espace bidimensionnel.

    Paramètres :
    - x (float) : La coordonnée x du point.
    - y (float) : La coordonnée y du point.

    Méthodes :
    - __str__() : Renvoie une représentation textuelle du point au format WKT.
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"POINT ({self.x} {self.y})"


class LineString:
    """
    Représente une séquence ordonnée de points formant une polyligne.

    Paramètres :
    - points (List[Point]) : La liste des points formant la polyligne.

    Méthodes :
    - __str__() : Renvoie une représentation textuelle de la polyligne au format WKT.
    """
    def __init__(self, points):
        if len(points) < 2:
            raise ValueError("Une LineString doit avoir au moins deux points.")
        self.points = points

    def __str__(self):
        return "LINESTRING (" + ", ".join(f"{point.x} {point.y}" for point in self.points) + ")"


class Polygon:
    """
    Représente une figure géométrique bidimensionnelle délimitée par une séquence ordonnée de points.

    Paramètres :
    - points (List[Point]) : La liste des points formant le polygone.

    Méthodes :
    - __str__() : Renvoie une représentation textuelle du polygone au format WKT.
    """
    def __init__(self, points):
        if len(points) < 3:
            raise ValueError("Un polygone doit avoir au moins trois points.")
        self.points = points

    def __str__(self):
        return "POLYGON ((" + ", ".join(f"{point.x} {point.y}" for point in self.points) + "))"


def create_wkt_object_from_string(coord_string):
    """
    Crée un objet WKT (Well-Known Text) à partir d'une chaîne de coordonnées.

    Paramètres :
    - coord_string (str) : Une chaîne de caractères représentant des coordonnées.

    Retourne :
    - str : Une représentation textuelle WKT de l'objet.

    La fonction analyse la chaîne de coordonnées et crée un objet WKT correspondant, pouvant être un Point, une LineString
    ou un Polygon. Elle renvoie une représentation textuelle WKT de l'objet créé. Pour différencier un polygone d'une
    simple polyligne, nous considérons qu'un polygone est une polyligne dont le dernier point est confondu avec le premier'

    Exemples de coord_string :
    - "40.0, 20.0" : Crée un Point avec les coordonnées (20.0, 40.0).
    - "40.0, 20.0\n30.0, 10.0\n20.0, 30.0\n40.0, 20.0" : Crée un Polygon avec une séquence de points.
    - "40.0, 20.0\n30.0, 10.0\n20.0, 30.0" : Crée une LineString avec une séquence de points.
    """
    lines = coord_string.split('\n')
    coords = []
    for line in lines:
        if line.strip():
            coords.extend([float(coord) for coord in line.split(',')])

    if len(coords) == 2:
        return str(Point(coords[1], coords[0]))
    elif len(coords) > 4 and len(coords) % 2 == 0 and coords[0] == coords[-2] and coords[1] == coords[-1]:
        points = [Point(coords[i + 1], coords[i]) for i in range(0, len(coords), 2)]
        return str(Polygon(points))
    elif len(coords) >= 4 and len(coords) % 2 == 0:
        return str(LineString([Point(coords[i + 1], coords[i]) for i in range(0, len(coords), 2)]))
    else:
        raise ValueError("La liste de coordonnées n'est pas valide pour former un objet WKT.")


def get_classe(root, element):
    """
    Construit un DataFrame à partir d'un élément spécifique dans une structure XML représentée par un objet ElementTree.

    Paramètres :
    - root (ElementTree.Element) : L'élément racine de la structure XML.
    - element (str) : Le nom de l'élément spécifique à extraire.

    Retourne :
    - pd.DataFrame : Un DataFrame Pandas contenant les données de l'élément spécifié.

    La fonction parcourt la structure XML à partir de l'élément racine (root) et recherche l'élément spécifié (element).
    Elle extrait les données de chaque enfant de l'élément trouvé, construit un tableau de données (data) et crée un DataFrame
    avec Pandas. Chaque colonne du DataFrame correspond à un attribut trouvé dans les enfants de l'élément, et chaque ligne
    représente les valeurs associées à ces attributs pour chaque enfant.

    Remarque : Les valeurs manquantes dans le DataFrame sont représentées par np.nan (numpy.nan).
    """
    
    cols = []
    data = []

    for classe in root[0]:
        if classe.tag == element:
            #construction collonnes
            for child in classe:
                for attributs in child:
                    if child.tag not in cols:
                        cols.append(child.tag)
                    elif attributs.tag not in cols:
                        cols.append(attributs.tag)
            nb_cols = len(cols)
            #construction de data
            for child in classe:
                #initialisation de la ligne
                line = [np.nan]*nb_cols
                for attributs in child:
                    #récupération du numéro de la collone             
                    for i in range(nb_cols):
                        if attributs.tag == cols[i]:
                            if attributs.text == None:
                                line[i] = attributs.attrib
                            else:
                                line[i] = attributs.text
                line[0] = child.attrib
                data.append(line)
                                
    df = pd.DataFrame(data = data,columns = cols)
    return df


def construct_BDD_espaces(root):
    """
    Construit un DataFrame avec le formalisme de la base de donnée à créer à partir d'une structure XML.

    Paramètres :
    - root (ElementTree.Element) : L'élément racine de la structure XML.

    Retourne :
    - pd.DataFrame : Un DataFrame Pandas contenant les informations extraites.

    La fonction utilise la fonction get_classe pour extraire des DataFrames spécifiques ('df_espaces', 'df_parties',
    'df_volumes') à partir de l'élément racine de la structure XML. Ensuite, elle parcourt ces DataFrames pour construire
    un nouveau DataFrame ('data').

    Chaque ligne du DataFrame final représente un volume associé à une partie qui, à son tour, est associée à
    un espace. Les colonnes incluent des informations spécifiques à chaque niveau (Espace, Partie, Volume), ainsi qu'une
    colonne 'Type' pour indiquer le type de données (Volume).
    """
    
    df_espaces = get_classe(root,'EspaceS')
    df_parties = get_classe(root,'PartieS')
    df_volumes = get_classe(root,'VolumeS')
    
    
    data = pd.DataFrame([])
    
    #Pour chaque espace on stoque ses infos et on garde son identifiant
    for espace in df_espaces.index:
        
        nom_espace = df_espaces.loc[espace,"Espace"]
        line_espace = df_espaces.loc[espace:espace].reset_index(drop=True)
        
        #Construction du dataframe contenant toutes les parties de cet espace
        df_parties_espace = df_parties.query("Espace == @nom_espace")
        
        #Pour chaque partie on stoque ses infos et on garde son identifiant
        for partie in df_parties_espace.index:
           
            nom_partie = df_parties_espace.loc[partie,"Partie"]
            line_partie = df_parties_espace.loc[partie:partie].reset_index(drop=True).drop(columns="Espace")
            
            #Construction du dataframe contenant toutes les parties de cet espace
            df_volumes_partie = df_volumes.query("Partie == @nom_partie")
            
            #Pour chaque volume ayant comme partie associé l'id de la partie observé, alors on stoque ses infos
            for volume in df_volumes_partie.index:
                line_volume = df_volumes_partie.loc[volume:volume].reset_index(drop=True).drop(columns="Partie")
                        
                #On construit la ligne associé à ce volume
                type_df = pd.DataFrame({"Type": ["Volume"]})
                line = pd.concat([type_df,line_espace,line_partie,line_volume], axis=1)
                data = pd.concat([data, line], ignore_index=True)
                        
    return data


def ajout_lk(dataframe):
    """
    Ajoute une colonne 'lk' à un DataFrame en extrayant la valeur contenu dans l'identifiant de chaque objet.

    Paramètres :
    - dataframe (pd.DataFrame) : Le DataFrame auquel ajouter la colonne 'lk'.

    Retourne :
    - pd.DataFrame : Le DataFrame modifié avec la nouvelle colonne 'lk' ajoutée.

    La fonction parcourt chaque ligne du DataFrame et extrait dans un premier temps le type de l'objet étudié. Cela permet 
    d'aller chercher son identifiant dans la colonne du même nom que son type. Cette colonne doit contenir un 
    dictionnaire (au format string) contenant la clé 'lk' à récupérer.
    La valeur extraite est ensuite ajoutée dans une nouvelle colonne 'lk' du DataFrame.

    Remarque : La fonction utilise ast.literal_eval pour évaluer la chaîne de caractères représentant un dictionnaire
    Python.
    """
    
    for line in dataframe.index:
        type_line = dataframe.loc[line,"Type"]
        pk = ast.literal_eval(dataframe.loc[line,type_line])
        lk = pk['lk']
        dataframe.loc[line, "lk"] = lk
    
    return dataframe


def construct_BDD(root):
    """
    Construit un DataFrame représentant une base de données globale à partir d'une structure XML.

    Paramètres :
    - root (ElementTree.Element) : L'élément racine de la structure XML.

    Retourne :
    - pd.DataFrame : Un DataFrame Pandas contenant les informations extraites.

    La fonction utilise la fonction construct_BDD_espaces pour extraire les informations spécifiques aux espaces de la
    structure XML. Ensuite, elle utilise la fonction get_classe pour extraire les informations relatives aux points de
    navigation ('NavFixS').

    Les données relatives aux points de navigation sont marquées avec un type 'NavFix' dans la colonne 'Type' du DataFrame
    correspondant.

    Enfin, les DataFrames extraits sont concaténés et une colonne 'lk' est ajoutée en utilisant la fonction ajout_lk.

    Remarque : La fonction convertit temporairement le DataFrame en chaînes de caractères pour éviter des problèmes de
    type lors de la concaténation.
    """
    
    df_bdd_espace = construct_BDD_espaces(root)
    df_navfixs = get_classe(root,'NavFixS')
    
    for navfix in df_navfixs.index:
        df_navfixs.loc[navfix,"Type"] = "NavFix"
    
    data = pd.concat([df_bdd_espace, df_navfixs], ignore_index=True)
    data = data.astype(str)
    data = ajout_lk(data)
    
    return data


def create_database(path, filename, conn_params):
    """
    Crée une base de données PostgreSQL à partir d'un fichier XML contenant des données géospatiales.

    Parameters:
    - path (str): Le chemin vers le répertoire du fichier XML.
    - filename (str): Le nom du fichier XML contenant les données géospatiales.
    - conn_params (dict): Les paramètres de connexion à la base de données PostgreSQL, sous la forme d'un dictionnaire
                         avec les clés 'host', 'port', 'user', 'password', et 'database'.

    Returns:
    None

    Steps:
    1. Parses le fichier XML spécifié.
    2. Construit la base de données à partir des éléments du fichier XML.
    3. Ajoute une colonne 'wkt' à la base de données en utilisant la fonction create_wkt_object_from_string.
    4. Convertit la base de données en un GeoDataFrame avec GeoPandas.
    5. Établit une connexion PostgreSQL en utilisant les paramètres spécifiés.
    6. Utilise SQLAlchemy pour créer un moteur de base de données.
    7. Renomme la table en remplaçant les tirets par des underscores dans le nom du fichier.
    8. Convertit le GeoDataFrame en une table PostgreSQL dans la base de données.
    9. Ferme la connexion à la base de données.

    Note:
    - La fonction utilise les bibliothèques ElementTree, GeoPandas, psycopg2, et SQLAlchemy.
    """
    
    # parsing
    tree_xml = ET.parse(str(path)+str(filename))
    
    # get the parent tag
    root_xml = tree_xml.getroot()
    
    # construction de la bdd avec Espaces + NavFixs
    BDD = construct_BDD(root_xml)
    
    # ajout de la colonne wkt et conversion de pandas en geopandas
    BDD["wkt"] = BDD.Geometrie.apply(create_wkt_object_from_string)
    gdf = gpd.GeoDataFrame(BDD,
                           geometry=gpd.GeoSeries.from_wkt(BDD.wkt),
                           crs="EPSG:4326")
    
    # connexion postgres
    conn = psycopg2.connect(**conn_params)
    
    # utiliser SQLAlchemy pour créer un moteur de base de données
    engine = create_engine(f"postgresql+psycopg2://{conn_params['user']}:{conn_params['password']}@{conn_params['host']}:{conn_params['port']}/{conn_params['database']}")

    # nomer la table en remplaçant les "-" par "_"
    table_name = ""
    for car in filename:
        if car == '-':
            table_name += "_"
        else:
            table_name += car
    table_name = table_name[:-4]
    
    # convertir le DataFrame en table PostgreSQL
    gdf.to_postgis(table_name, engine, if_exists='replace', index=True, index_label="pk")

    # fermer la connexion à la base de données
    conn.close()
    
    return



### ------------------------    Main    ------------------------ ###

if __name__ == "__main__":
    
    ### ------------------------    Parsing with ETREE    ------------------------ ###
    
    # pass the path of the xml document 
    path_10 = 'Donnees SIA/export_xml_bd_sia_2023-10-05-s2/'
    path_11 = 'Donnees SIA/export_xml_bd_sia_2023-11-02-c1/'
    path_01 = 'Donnees SIA/export_xml_bd_sia_2024-01-25-u6/'
    path_02 = 'Donnees SIA/export_xml_bd_sia_2024-02-22-h9/'
    
    # pass the filename of the xml document 
    file_10 = 'XML_SIA_2023-10-05.xml'
    file_11 = 'XML_SIA_2023-11-02.xml'
    file_01 = 'XML_SIA_2024-01-25.xml'
    file_02 = 'XML_SIA_2024-02-22.xml'
    
    # connexion postgres
    conn_params = {
        'database' : "projet_BEA",
        'user' : "postgres",
        'host': "localhost",
        'password' : "proj_bea",
        'port' : 5432
    }

    # conn_params = {
    #     'database' : "projet_BEA",
    #     'user': "jfv",
    #     'host': "localhost",
    #     'password': "",
    #     'port': 5432
    # }
    
    # execution de la pipeline
    create_database(path_10, file_10, conn_params)
    create_database(path_11, file_11, conn_params)
    create_database(path_01, file_01, conn_params)
    create_database(path_02, file_02, conn_params)