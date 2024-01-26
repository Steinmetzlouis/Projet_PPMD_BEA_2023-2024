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
from sqlalchemy import create_engine
#os.system(wget_request)
# wget_request = 'wget --user={} --password={} --load-cookies {}  --save-cookies {}  --auth-no-challenge=on --keep-session-cookies -P {} --content-disposition  {}'



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


def construct_BDDG_ad(root):
    
    df_ad = get_classe(root,'AdS')
    df_vorinschk = get_classe(root,'VorInsChkS')
    df_rwy = get_classe(root,'RwyS')
    df_ils = get_classe(root,'IlsS')
    df_rwylgt = get_classe(root,'RwyLgtS')
    df_twydecdist = get_classe(root,'TwyDecDistS')
    df_dmeils = get_classe(root,'DmeIlsS')
    df_gp = get_classe(root,'GpS')
    df_mkr = get_classe(root,'MkrS')
    
    data_ad = pd.DataFrame([])
    data_vorinschk = pd.DataFrame([])
    data_rwy = pd.DataFrame([])
    data_rwylgt = pd.DataFrame([])
    data_twydecdist = pd.DataFrame([])
    data_ils = pd.DataFrame([])
    data_dmeils = pd.DataFrame([])
    data_gp = pd.DataFrame([])
    data_mkr = pd.DataFrame([])
    c=0
    
    #Pour chaque aérodrome on stoque ses infos et on garde son identifiant
    for ad in df_ad.index:
        
        nom_ad = df_ad.loc[ad,"Ad"]
        line_ad = df_ad.loc[ad:ad].reset_index(drop=True)
        
        #Construction du dataframe contenant tous les vorinschk de cet aérodrome
        df_vorinschk_ad = df_vorinschk.query("Ad == @nom_ad")
        #Construction du dataframe contenant tous les runway de cet aérodrome
        df_rwy_ad = df_rwy.query("Ad == @nom_ad")
        
        if df_vorinschk_ad.shape[0] != 0:
            for vorinschk in df_vorinschk_ad.index:
                line_vorinschk = df_vorinschk_ad.loc[vorinschk:vorinschk].reset_index(drop=True).drop(columns="Ad")
                
                #On construit la ligne associé à ce vorinschk
                type_df = pd.DataFrame({"Type": ["VorInsChk"]})
                line = pd.concat([type_df,line_ad,line_vorinschk], axis=1)
                data_vorinschk = pd.concat([data_vorinschk, line], ignore_index=True)
                
        if df_rwy_ad.shape[0] != 0:
        
            #Pour chaque runway on stoque ses infos et on garde son identifiant
            for rwy in df_rwy_ad.index:
           
                nom_rwy = df_rwy_ad.loc[rwy,"Rwy"]
                line_rwy = df_rwy_ad.loc[rwy:rwy].reset_index(drop=True).drop(columns="Ad")
                
                #Construction des dataframe issus de cette runway
                df_ils_rwy = df_ils.query("Rwy == @nom_rwy")
                df_rwylgt_rwy = df_rwylgt.query("Rwy == @nom_rwy")
                df_twydecdist_rwy = df_twydecdist.query("Rwy == @nom_rwy")
                
                if df_rwylgt_rwy.shape[0] != 0:
                    for rwylgt in df_rwylgt_rwy.index:
                        line_rwylgt = df_rwylgt_rwy.loc[rwylgt:rwylgt].reset_index(drop=True).drop(columns="Rwy")
                        
                        #On construit la ligne associé à ce vorinschk
                        type_df = pd.DataFrame({"Type": ["RwyLgt"]})
                        line = pd.concat([type_df,line_ad,line_rwy,line_rwylgt], axis=1)
                        data_rwylgt = pd.concat([data_rwylgt, line], ignore_index=True)
                        
                if df_twydecdist_rwy.shape[0] != 0:
                    for twydecdist in df_twydecdist_rwy.index:
                        line_twydecdist = df_twydecdist_rwy.loc[twydecdist:twydecdist].reset_index(drop=True).drop(columns="Rwy")
                        
                        #On construit la ligne associé à ce vorinschk
                        type_df = pd.DataFrame({"Type": ["TwyDecDist"]})
                        line = pd.concat([type_df,line_ad,line_rwy,line_twydecdist], axis=1)
                        data_twydecdist = pd.concat([data_twydecdist, line], ignore_index=True)
                        
                if df_ils_rwy.shape[0] != 0:
                    for ils in df_ils_rwy.index:
                   
                        nom_ils = df_ils_rwy.loc[ils,"Ils"]
                        line_ils = df_ils_rwy.loc[ils:ils].reset_index(drop=True).drop(columns="Rwy")
                        
                        #Construction des dataframe issus de cet ils
                        df_dmeils_ils = df_dmeils.query("Ils == @nom_ils")
                        df_gp_ils = df_gp.query("Ils == @nom_ils")
                        df_mkr_ils = df_mkr.query("Ils == @nom_ils")
                        
                        if df_dmeils_ils.shape[0] != 0:
                            for dmeils in df_dmeils_ils.index:
                                line_dmeils = df_dmeils_ils.loc[dmeils:dmeils].reset_index(drop=True).drop(columns="Ils")
                                
                                #On construit la ligne associé à ce dmeils
                                type_df = pd.DataFrame({"Type": ["DmeIls"]})
                                line = pd.concat([type_df,line_ad,line_rwy,line_ils,line_dmeils], axis=1)
                                data_dmeils = pd.concat([data_dmeils, line], ignore_index=True)
                                
                        if df_gp_ils.shape[0] != 0:
                            for gp in df_gp_ils.index:
                                line_gp = df_gp_ils.loc[gp:gp].reset_index(drop=True).drop(columns="Ils")
                                
                                #On construit la ligne associé à ce dmeils
                                type_df = pd.DataFrame({"Type": ["Gp"]})
                                line = pd.concat([type_df,line_ad,line_rwy,line_ils,line_gp], axis=1)
                                data_gp = pd.concat([data_gp, line], ignore_index=True)
                                
                        if df_mkr_ils.shape[0] != 0:
                            for mkr in df_mkr_ils.index:
                                line_mkr = df_mkr_ils.loc[mkr:mkr].reset_index(drop=True).drop(columns="Ils")
                                
                                #On construit la ligne associé à ce dmeils
                                type_df = pd.DataFrame({"Type": ["Mkr"]})
                                line = pd.concat([type_df,line_ad,line_rwy,line_ils,line_mkr], axis=1)
                                data_mkr = pd.concat([data_mkr, line], ignore_index=True)
                         
                        # Cas où l'Ils n'a ni dmeils, ni gp, ni mkr
                        if df_dmeils_ils.shape[0] == 0 and df_gp_ils.shape[0] == 0 and df_mkr_ils.shape[0] == 0:
                            #On construit la ligne associé à ce ils
                            type_df = pd.DataFrame({"Type": ["Ils"]})
                            line = pd.concat([type_df,line_ad,line_rwy,line_ils], axis=1)
                            data_ils = pd.concat([data_ils, line], ignore_index=True)
                            
                # Cas où la piste n'a ni Ils, ni RwyLgt, ni TwyDecDist
                if df_rwylgt_rwy.shape[0] == 0 and df_twydecdist_rwy.shape[0] == 0 and df_ils_rwy.shape[0] == 0:
                    #On construit la ligne associé à ce vorinschk
                    type_df = pd.DataFrame({"Type": ["Rwy"]})
                    line = pd.concat([type_df,line_ad,line_rwy], axis=1)
                    data_rwy = pd.concat([data_rwy, line], ignore_index=True)
                
            # Cas où l'aérodrome n'a ni Rwy, ni VorInsChk
            if df_vorinschk_ad.shape[0] == 0 and df_rwy_ad.shape[0] == 0:
                #On construit la ligne associé à ce ad
                type_df = pd.DataFrame({"Type": ["Ad"]})
                line = pd.concat([type_df,line_ad], axis=1)
                data_ad = pd.concat([data_ad, line], ignore_index=True)
                
    data_ad = data_ad.reset_index(drop=True)
    data_vorinschk = data_vorinschk.reset_index(drop=True)
    data_rwy = data_rwy.reset_index(drop=True)
    data_rwylgt = data_rwylgt.reset_index(drop=True)
    data_twydecdist = data_twydecdist.reset_index(drop=True)
    data_ils = data_ils.reset_index(drop=True)
    data_dmeils = data_dmeils.reset_index(drop=True)
    data_gp = data_gp.reset_index(drop=True)
    data_mkr = data_mkr.reset_index(drop=True)
        
    # data = pd.concat([data_ad, data_vorinschk],ignore_index=True)
    # data = pd.concat([data_ad, data_vorinschk, data_rwy, data_rwylgt, data_twydecdist, data_ils, data_dmeils, data_gp, data_mkr], ignore_index=True)
    # return data
    return data_ad, data_vorinschk, data_rwy, data_rwylgt, data_twydecdist, data_ils, data_dmeils, data_gp, data_mkr



def construct_BDDG(root):
    
    df_bddg_espace = construct_BDDG_espaces(root)
    df_navfixs = get_classe(root,'NavFixS')
    
    for navfix in df_navfixs.index:
        df_navfixs.loc[navfix,"Type"] = "NavFix"
    
    data = pd.concat([df_bddg_espace, df_navfixs], ignore_index=True)
    data = data.astype(str)
    
    return data



### ------------------------    Main    ------------------------ ###

if __name__ == "__main__":
    
    ### ------------------------    Parsing with ETREE    ------------------------ ###
    
    # pass the path of the xml document 
    path = 'Donnees SIA/export_xml_bd_sia_2023-10-05-s2/'
    tree_SIA_10 = ET.parse(str(path)+'XML_SIA_2023-10-05.xml')
    tree_donees_test = ET.parse('donnees_test_v2.xml')

    # get the parent tag
    root_SIA_10 = tree_SIA_10.getroot()
    root_donees_test = tree_donees_test.getroot()
    
    # test fonctions
    # df_espaces = get_classe(root_SIA_10,'EspaceS')
    # df_espaces_test = get_classe(root_donees_test,'EspaceS')
    
    # df_parties_test = get_classe(root_donees_test,'PartieS')
    # df_parties = get_classe(root_SIA_10,'PartieS')
    
    # df_volumes_test = get_classe(root_donees_test,'VolumeS')
    # df_volumes = get_classe(root_SIA_10,'VolumeS')
    
    df_territoires_test = get_classe(root_donees_test,'TerritoireS')
    df_territoires = get_classe(root_SIA_10,'TerritoireS')
    
    df_ad = get_classe(root_SIA_10,'AdS')
    df_vorinschk = get_classe(root_SIA_10,'VorInsChkS')
    df_rwy = get_classe(root_SIA_10,'RwyS')
    df_ils = get_classe(root_SIA_10,'IlsS')
    df_rwylgt = get_classe(root_SIA_10,'RwyLgtS')
    df_twydecdist = get_classe(root_SIA_10,'TwyDecDistS')
    df_dmeils = get_classe(root_SIA_10,'DmeIlsS')
    df_gp = get_classe(root_SIA_10,'GpS')
    df_mkr = get_classe(root_SIA_10,'MkrS')
    
    # BDDG_espaces_test = construct_BDDG_espaces(root_donees_test)
    # BDDG_espaces = construct_BDDG_espaces(root_SIA_10)
    
    # BDDG_ad = construct_BDDG_ad(root_SIA_10)
    data_ad, data_vorinschk, data_rwy, data_rwylgt, data_twydecdist, data_ils, data_dmeils, data_gp, data_mkr = construct_BDDG_ad(root_SIA_10)
    mon_path='../../../'
    data_vorinschk.to_pickle(mon_path+'df_vorinschk')
    data_rwy.to_pickle(mon_path+'df_rwy')
    
    
    # BDDG_test = construct_BDDG(root_donees_test)
    # gdf = gpd.GeoDataFrame(BDDG_test,
    #                        geometry=gpd.points_from_xy(BDDG_test.Longitude, BDDG_test.Latitude),
    #                        crs="EPSG:4326")
    # gdf = gpd.GeoDataFrame(BDDG_test,
    #                        geometry=gpd.GeoSeries.from_wkt(BDDG_test.Longitude, BDDG_test.Latitude),
    #                        crs="EPSG:4326")
    BDDG = construct_BDDG(root_SIA_10)
    # gdf = gpd.GeoDataFrame(BDDG,
    #                        geometry=gpd.points_from_xy(BDDG.Longitude, BDDG.Latitude),
    #                        crs="EPSG:4326")
    # print(BDDG.Geometrie)

    BDDG["wkt"] = BDDG.Geometrie.apply(create_wkt_object_from_string)
    gdf = gpd.GeoDataFrame(BDDG,
                           geometry=gpd.GeoSeries.from_wkt(BDDG.wkt),
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
    table_name = 'XML_SIA_2023-10-05'
    # BDDG_test.to_sql(table_name, engine, if_exists='replace', index=False)

    gdf.to_postgis(table_name, engine, if_exists='replace', index=False)
    
    # BDDG.to_sql(table_name, engine, if_exists='replace', index=False)

    # Fermer la connexion à la base de données
    conn.close()