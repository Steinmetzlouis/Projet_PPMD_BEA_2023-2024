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
                    





### ------------------------    With ETREE    ------------------------ ###
# Pass the path of the xml document 
path = 'Donnees SIA/export_xml_bd_sia_2023-10-05-s2/'
tree_SIA_10 = ET.parse(str(path)+'XML_SIA_2023-10-05.xml')
path_donnee_test = 'Dev/'
tree_donees_test = ET.parse(str(path_donnee_test)+'donnees_test_v2.xml')

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
df_espace_test = get_espace(root_donees_test) 


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