# imports
import psycopg2
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup as be
import pandas as pd




### ------------------------    Fonctions    ------------------------ ###

def get_espace(root):
    
    cols = []
    data = []
    c = 0

    for classe in root[0]:
        if classe.tag == 'EspaceS':
            for espace in classe:
                line = []
                if espace.tag not in cols:
                    cols.append(espace.tag)
                line.append(espace.attrib)
                
                for attributs in espace:
                    if attributs.text == None:
                        if attributs.tag not in cols:
                            cols.append(attributs.tag)
                        line.append(attributs.attrib)
                    else:
                        if attributs.tag not in cols:
                            cols.append(attributs.tag)
                        line.append(attributs.text)
                        
                data.append(line)
                print('line: ',line)
                c += 1
                if c > 1000:
                    break
                
    # print('data: ',data)
    print('cols: ',cols)
    df = pd.DataFrame(data = data,columns = cols)
    return df


def get_espace2(root):
    
    cols = []
    data = []
    c = 0

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
                c += 1
                if c > 1000:
                    break
                                
    # print('data: ',data)
    print('cols: ',cols)
    df = pd.DataFrame(data = data,columns = cols)
    return df
                    



def construct_BDDG_espaces(root):
    
    df_espaces = get_espaces(root)
    df_parties = get_parties(root)
    df_volumes = get_volumes(root)
    
    data = pd.DataFrame([])
    L=[]
    #Pour chaque espace on stoque ses infos et on garde son identifiant
    for espace in df_espaces.index:
        nom_espace = df_espaces.loc[espace,"Espace"]
        print('nom_espace: ',nom_espace)
        line_espace = df_espaces[espace:espace+1]
        
        #Pour chaque partie ayant comme espace associé l'id de l'espace observé, alors on stoque ses infos et on garde son identifiant
        for partie in df_parties.index:
            if (df_parties.loc[partie,"Espace"] == nom_espace) == True:
                nom_partie = df_parties.loc[partie,"Partie"]
                print('nom_partie: ',nom_partie)
                line_partie = df_parties.loc[partie:partie+1]
                print('line_partie: ',line_partie)
                #Pour chaque volume ayant comme partie associé l'id de la partie observé, alors on stoque ses infos
                for volume in df_volumes.index:
                    if (df_volumes.loc[volume,"Partie"] == nom_partie) == True:
                        line_volume = df_volumes[volume:volume+1]
                        
                        #On construit la ligne associé à ce volume
                        # type_df = pd.DataFrame(data = ["Volume"],columns = ["Type"])
                        type_df = pd.DataFrame({"Type": ["Volume"]})
                        line = pd.concat([type_df,line_espace,line_partie,line_volume], ignore_index=True, axis=1)
                        # line = pd.concat([type_df,line_espace], ignore_index=True, axis=1)
                        L.append(line)
                        data = pd.concat([data, line], ignore_index=True)
                        
    return data,L




### ------------------------    With ETREE    ------------------------ ###
# Pass the path of the xml document 
path = 'Donnees SIA/export_xml_bd_sia_2023-10-05-s2/'
tree_SIA_10 = ET.parse(str(path)+'XML_SIA_2023-10-05.xml')
tree_donees_test = ET.parse('donnees_test_v2.xml')

# get the parent tag
root_SIA_10 = tree_SIA_10.getroot()
root_donees_test = tree_donees_test.getroot()

#test
situation_SIA_10 = root_SIA_10[0]
c=0
for elt in situation_SIA_10:
    if elt.tag == 'EspaceS':
        # Récupération du deuxième espace:
        espace1 = elt[1]
        print(espace1.tag, ': ', espace1.attrib)
        for attributs in espace1:
            if attributs.text == None:
                print(attributs.tag, ': ' ,attributs.attrib)
            else:
                print(attributs.tag, ': ' ,attributs.text)
               
        # # Récupération de tous les espaces complets (AltrFt and AdAssocie not null):
        # for espace in elt:
        #     for attributs in espace:
        #         if attributs.tag == 'AltrFt' and attributs.text != None:
        #             print('\n', espace.tag, ': ', espace.attrib)
        #             for attributs in espace:
        #                 if attributs.text == None:
        #                     print(attributs.tag, ': ' ,attributs.attrib)
        #                 else:
        #                     print(attributs.tag, ': ' ,attributs.text)
        #             break
        
    elif elt.tag == 'PartieS':
        # Récupération de la deuxième partie:
        partie1 = elt[1]
        print('\n', partie1.tag, ': ', partie1.attrib)
        for attributs in partie1:
            if attributs.text == None:
                print(attributs.tag, ': ' ,attributs.attrib)
            else:
                print(attributs.tag, ': ' ,attributs.text)
                
    elif elt.tag == 'VolumeS':
        # Récupération du deuxième volume:
        volume1 = elt[1]
        print('\n', volume1.tag, ': ', volume1.attrib)
        for attributs in volume1:
            if attributs.text == None:
                print(attributs.tag, ': ' ,attributs.attrib)
            else:
                print(attributs.tag, ': ' ,attributs.text)
                
    elif elt.tag == 'NavFixS':
        # Récupération du deuxième NavFix:
        navfix1 = elt[19]
        print('\n', navfix1.tag, ': ', navfix1.attrib)
        for attributs in navfix1:
            if attributs.text == None:
                print(attributs.tag, ': ' ,attributs.attrib)
            else:
                print(attributs.tag, ': ' ,attributs.text)
                
        ## Test pour savoir s'il y a d'autres valeurs que 2:
        for navfix in elt:
            for attributs in navfix:
                if attributs.tag == 'Wgs84' and type(attributs.text) is not str:
                    print(attributs.text)
        
            
# df_espace = get_espace(root_SIA_10)
df_espace = get_espace2(root_SIA_10)
# df_espace_test = get_espace(root_donees_test) 
df_espace_test = get_espace2(root_donees_test) 
# df_espaces_test_line3 = df_espaces_test[3:4]


### ------------------------    With BeautifulSoup    ------------------------ ###
# soup = be(str(path)+'XML_SIA_2023-10-05.xml', 'html.parser')




### ------------------------    With psycopg2    ------------------------ ###
# # Code for connecting to a dtb postgresql:
# conn = psycopg2.connect(
# 					user = "postgres",
# 					password = "postgres",
# 					host = "localhost",
# 					port = "5432",
# 					database = "my_db"
#     )
# cur = conn.cursor()