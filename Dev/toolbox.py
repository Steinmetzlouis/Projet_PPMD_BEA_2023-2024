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
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"POINT ({self.x} {self.y})"


class LineString:
    def __init__(self, points):
        if len(points) < 2:
            raise ValueError("Une LineString doit avoir au moins deux points.")
        self.points = points

    def __str__(self):
        return "LINESTRING (" + ", ".join(f"{point.x} {point.y}" for point in self.points) + ")"


class Polygon:
    def __init__(self, points):
        if len(points) < 3:
            raise ValueError("Un polygone doit avoir au moins trois points.")
        self.points = points

    def __str__(self):
        return "POLYGON ((" + ", ".join(f"{point.x} {point.y}" for point in self.points) + "))"


def create_wkt_object_from_string(coord_string):
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


def construct_BDDG_espaces(root):
    
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
    
    for line in dataframe.index:
        type_line = dataframe.loc[line,"Type"]
        pk = ast.literal_eval(dataframe.loc[line,type_line])
        lk = pk['lk']
        dataframe.loc[line, "lk"] = lk
    
    return dataframe


def construct_BDDG(root):
    
    df_bddg_espace = construct_BDDG_espaces(root)
    df_navfixs = get_classe(root,'NavFixS')
    
    for navfix in df_navfixs.index:
        df_navfixs.loc[navfix,"Type"] = "NavFix"
    
    data = pd.concat([df_bddg_espace, df_navfixs], ignore_index=True)
    data = data.astype(str)
    data = ajout_lk(data)
    
    return data



### ------------------------    Main    ------------------------ ###

if __name__ == "__main__":
    
    ### ------------------------    Parsing with ETREE    ------------------------ ###
    
    # pass the path of the xml document 
    path_10 = 'Donnees SIA/export_xml_bd_sia_2023-10-05-s2/'
    path_11 = 'Donnees SIA/export_xml_bd_sia_2023-11-02-c1/'
    path_01 = 'Donnees SIA/export_xml_bd_sia_2024-01-25-u6/'
    path_02 = 'Donnees SIA/export_xml_bd_sia_2024-02-22-h9/'
    
    # parsing
    tree_SIA_10 = ET.parse(str(path_10)+'XML_SIA_2023-10-05.xml')
    tree_SIA_11 = ET.parse(str(path_11)+'XML_SIA_2023-11-02.xml')
    tree_SIA_01 = ET.parse(str(path_01)+'XML_SIA_2024-01-25.xml')
    tree_SIA_02 = ET.parse(str(path_02)+'XML_SIA_2024-02-22.xml')

    # get the parent tag
    root_SIA_10 = tree_SIA_10.getroot()
    root_SIA_11 = tree_SIA_11.getroot()
    root_SIA_01 = tree_SIA_01.getroot()
    root_SIA_02 = tree_SIA_02.getroot()
    
    # construction de la bdd avec Espaces + NavFixs
    BDDG_10 = construct_BDDG(root_SIA_10)
    BDDG_11 = construct_BDDG(root_SIA_11)
    BDDG_01 = construct_BDDG(root_SIA_01)
    BDDG_02 = construct_BDDG(root_SIA_02)

    # ajout de la colonne wkt et conversion de pandas en geopandas
    BDDG_10["wkt"] = BDDG_10.Geometrie.apply(create_wkt_object_from_string)
    gdf_10 = gpd.GeoDataFrame(BDDG_10,
                           geometry=gpd.GeoSeries.from_wkt(BDDG_10.wkt),
                           crs="EPSG:4326")
    
    BDDG_11["wkt"] = BDDG_11.Geometrie.apply(create_wkt_object_from_string)
    gdf_11 = gpd.GeoDataFrame(BDDG_11,
                           geometry=gpd.GeoSeries.from_wkt(BDDG_11.wkt),
                           crs="EPSG:4326")
    
    BDDG_01["wkt"] = BDDG_01.Geometrie.apply(create_wkt_object_from_string)
    gdf_01 = gpd.GeoDataFrame(BDDG_01,
                           geometry=gpd.GeoSeries.from_wkt(BDDG_01.wkt),
                           crs="EPSG:4326")
    
    BDDG_02["wkt"] = BDDG_02.Geometrie.apply(create_wkt_object_from_string)
    gdf_02 = gpd.GeoDataFrame(BDDG_02,
                           geometry=gpd.GeoSeries.from_wkt(BDDG_02.wkt),
                           crs="EPSG:4326")
    
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
    
    conn = psycopg2.connect(**conn_params)

    # Utiliser SQLAlchemy pour créer un moteur de base de données
    engine = create_engine(f"postgresql+psycopg2://{conn_params['user']}:{conn_params['password']}@{conn_params['host']}:{conn_params['port']}/{conn_params['database']}")

    # Convertir le DataFrame en table PostgreSQL
    table_name_10 = 'XML_SIA_2023_10_05'
    gdf_10.to_postgis(table_name_10, engine, if_exists='replace', index=True, index_label="pk")
    
    table_name_11 = 'XML_SIA_2023_11_02'
    gdf_11.to_postgis(table_name_11, engine, if_exists='replace', index=True, index_label="pk")
    
    table_name_01 = 'XML_SIA_2024_01_25'
    gdf_01.to_postgis(table_name_01, engine, if_exists='replace', index=True, index_label="pk")
    
    table_name_02 = 'XML_SIA_2024_02_22'
    gdf_02.to_postgis(table_name_02, engine, if_exists='replace', index=True, index_label="pk")

    # Fermer la connexion à la base de données
    conn.close()