# -*- coding: utf-8 -*-
"""
Created on Sat Dec 16 15:18:45 2023

@author: lstei
"""


### ------------------------    Imports    ------------------------ ###
import xml.etree.ElementTree as ET
import pandas as pd




### ------------------------    Fonctions    ------------------------ ###

def get_espaces(root):
    
    cols = []
    data = []

    for classe in root[0]:
        if classe.tag == 'EspaceS':
            #construction collonnes
            for espace in classe:
                for attributs in espace:
                    if espace.tag not in cols:
                        cols.append(espace.tag)
                    elif attributs.tag not in cols:
                        cols.append(attributs.tag)
            nb_cols = len(cols)
            #construction de data
            for espace in classe:
                #initialisation de la ligne
                line = [None]*nb_cols
                line[0] = espace.attrib
                for attributs in espace:
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


def get_parties(root):
    
    cols = []
    data = []

    for classe in root[0]:
        if classe.tag == 'PartieS':
            #construction collonnes
            for partie in classe:
                for attributs in partie:
                    if partie.tag not in cols:
                        cols.append(partie.tag)
                    elif attributs.tag not in cols:
                        cols.append(attributs.tag)
            nb_cols = len(cols)
            #construction de data
            for partie in classe:
                #initialisation de la ligne
                line = [None]*nb_cols
                line[0] = partie.attrib
                for attributs in partie:
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


def get_volumes(root):
    
    cols = []
    data = []

    for classe in root[0]:
        if classe.tag == 'VolumeS':
            #construction collonnes
            for volume in classe:
                for attributs in volume:
                    if volume.tag not in cols:
                        cols.append(volume.tag)
                    elif attributs.tag not in cols:
                        cols.append(attributs.tag)
            nb_cols = len(cols)
            #construction de data
            for volume in classe:
                #initialisation de la ligne
                line = [None]*nb_cols
                line[0] = volume.attrib
                for attributs in volume:
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
    
    df_espaces = get_espaces(root)
    df_parties = get_parties(root)
    df_volumes = get_volumes(root)
    
    data = pd.DataFrame([])
    L=[]
    
    for espace in df_espaces.index:
        #    = [id,   Type]
        # line = [None, None]
        nom_espace = df_espaces.loc[espace,"Espace"]
        line_espace = df_espaces[espace:espace+1]
        for partie in df_parties.index:
            if df_parties.loc[partie,"Espace"] == nom_espace:
                nom_partie = df_parties.loc[partie,"Partie"]
                line_partie = df_espaces.loc[partie:partie+1]
                for volume in df_volumes.index:
                    if df_volumes.loc[partie,"Partie"] == nom_partie:
                        line_volume = df_volumes[volume:volume+1]
                        
                        type_df = pd.DataFrame(data = ["Volume"],columns = ["Type"])
                        print('type_df: ',type_df)
                        line = pd.concat([type_df,line_espace,line_partie,line_volume], ignore_index=True, axis=1)
                        L.append(line)
                        # line = pd.concat([line_espace,line_partie,line_volume], ignore_index=True)
                        data = pd.concat([data, line], ignore_index=True)
                        
    return data,L




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
    # df_espaces = get_espaces(root_SIA_10)
    # df_espaces_test = get_espaces(root_donees_test)
    # df_parties_test = get_parties(root_donees_test) 
    # df_volumes_test = get_volumes(root_donees_test)
    
    BDDG_espaces_test,L = construct_BDDG_espaces(root_donees_test)