# -*- coding: utf-8 -*-
"""
Created on Sat Dec 16 15:18:45 2023

@author: lstei
"""


### ------------------------    Imports    ------------------------ ###
import xml.etree.ElementTree as ET
import pandas as pd
#os.system(wget_request)
# wget_request = 'wget --user={} --password={} --load-cookies {}  --save-cookies {}  --auth-no-challenge=on --keep-session-cookies -P {} --content-disposition  {}'
# https://www.geeksforgeeks.org/how-to-insert-a-pandas-dataframe-to-an-existing-postgresql-table/



### ------------------------    Fonctions    ------------------------ ###

def get_classe(root, element):
    
    cols = []
    data = []

    for classe in root[0]:
        if classe.tag == element:
            #construction collonnes
            for espace in classe:
                for attributs in espace:
                    if espace.tag not in cols:
                        cols.append(espace.tag)
                    elif attributs.tag not in cols:
                        cols.append(attributs.tag)
            nb_cols = len(cols)
            #construction de data
            for childe in classe:
                #initialisation de la ligne
                line = [None]*nb_cols
                line[0] = childe.attrib
                for attributs in childe:
                    #récupération du numéro de la collone             
                    for i in range(nb_cols):
                        if attributs.tag == cols[i]:
                            if attributs.text == None:
                                line[i] = attributs.attrib
                            else:
                                line[i] = attributs.text
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
                nom_volume = df_volumes_partie.loc[volume,"Volume"]
                line_volume = df_volumes_partie.loc[volume:volume].reset_index(drop=True).drop(columns="Partie")
                        
                #On construit la ligne associé à ce volume
                type_df = pd.DataFrame({"Type": ["Volume"]})
                line = pd.concat([type_df,line_espace,line_partie,line_volume], axis=1)
                data = pd.concat([data, line], ignore_index=True)
                        
    return data


def construct_BDDG(root):
    
    df_bddg_espace = construct_BDDG_espaces(root)
    df_navfixs = get_classe(root,'NavFixS')
    
    for navfix in df_navfixs.index:
        df_navfixs.loc[navfix,"Type"] = "NavFix"
    
    data = pd.concat([df_bddg_espace, df_navfixs], ignore_index=True)
    
    return data




### ------------------------    Main    ------------------------ ###

if __name__ == "__main__":
    
    ### ------------------------    Parsing with ETREE    ------------------------ ###
    
    # Pass the path of the xml document 
    path = 'Donnees SIA/export_xml_bd_sia_2023-10-05-s2/'
    tree_SIA_10 = ET.parse(str(path)+'XML_SIA_2023-10-05.xml')
    tree_donees_test = ET.parse('donnees_test_v2.xml')

    # get the parent tag
    root_SIA_10 = tree_SIA_10.getroot()
    root_donees_test = tree_donees_test.getroot()
    
    #test fonctions
    df_espaces = get_classe(root_SIA_10,'EspaceS')
    df_espaces_test = get_classe(root_donees_test,'EspaceS')
    
    df_parties_test = get_classe(root_donees_test,'PartieS')
    df_parties = get_classe(root_SIA_10,'PartieS')
    
    df_volumes_test = get_classe(root_donees_test,'VolumeS')
    df_volumes = get_classe(root_SIA_10,'VolumeS')
    
    BDDG_espaces_test = construct_BDDG_espaces(root_donees_test)
    # BDDG_espaces = construct_BDDG_espaces(root_SIA_10)
    
    BDDG_test = construct_BDDG(root_donees_test)