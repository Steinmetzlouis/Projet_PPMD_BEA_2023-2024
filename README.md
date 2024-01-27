# Projet_PPMD_BEA_2023-2024

## Présentation du sujet
Dans le cadre des enquêtes de sécurité de l’aviation civile, le département technique du BEA travaille sur des données extraites d’enregistreurs de vol ou de calculateurs. Ces données sont analysées sur la base des informations réglementaires de l’aviation civile (carte VAC, zone de contrôle aérien, …). Le SIA met à disposition chaque mois une base de données actualisée au format XML contenant toutes les entités géographiques au format vectoriel. La documentation de ce format xml est disponible [ici](https://github.com/Steinmetzlouis/Projet_PPMD_BEA_2023-2024/blob/BDD/Dev/Donnees%20SIA/FAQZipExports/XML/siaexport6a.pdf).

Le premier objectif est de comprendre la nature et l’organisation des informations géographiques contenues dans les bases de données XML du SIA et d’y identifier les informations d’intérêt pour le BEA. Le second objectif est, à partir de cette base de données XML, de constituer un SGBD spatial interrogeable par les différents logiciels du BEA. Ce SGBD devra gérer les mises à jour des XML fournis par le SIA, leur archivage et permettre la consultation d’informations géographiques antérieures, contemporaines de la période où s’est produit l’accident ou l’incident aérien.

La présentation complète du sujet est à retrouver [ici](https://github.com/Steinmetzlouis/Projet_PPMD_BEA_2023-2024/blob/BDD/doc/PPMD_ProjetInfo_BEA_SGBD_SIA.pdf).


Toutes les bibliothèques nécessaires pour exécuter ces scripts Python sont résumées dans ce [fichier](https://github.com/Steinmetzlouis/Projet_PPMD_BEA_2023-2024/blob/BDD/Dev/requirements.txt)

## toolbox.py:
Script Python permettant la connexion à une base de données PostgreSQL et la création de 4 tables : une table par XML au format du SIA importé dans "Données SIA". Ces rapports sont ceux du :
* [2023-10-05](https://github.com/Steinmetzlouis/Projet_PPMD_BEA_2023-2024/blob/BDD/Dev/Donnees%20SIA/export_xml_bd_sia_2023-10-05-s2/XML_SIA_2023-10-05.xml)
* [2023-11-02](https://github.com/Steinmetzlouis/Projet_PPMD_BEA_2023-2024/blob/BDD/Dev/Donnees%20SIA/export_xml_bd_sia_2023-11-02-c1/XML_SIA_2023-11-02.xml)
* [2024-01-25](https://github.com/Steinmetzlouis/Projet_PPMD_BEA_2023-2024/blob/BDD/Dev/Donnees%20SIA/export_xml_bd_sia_2024-01-25-u6/XML_SIA_2024-01-25.xml)
* [2024-02-22](https://github.com/Steinmetzlouis/Projet_PPMD_BEA_2023-2024/blob/BDD/Dev/Donnees%20SIA/export_xml_bd_sia_2024-02-22-h9/XML_SIA_2024-02-22.xml)
  
Ce script est surtout utile pour initialiser une BDDG dans PostgreSQL avec plusieurs tables, notamment utile pour tester les fonctionnalités du plugin QGIS développé en parallèle de ce projet. La documentation développeur est la même que celle de [toolbox_v2](https://github.com/Steinmetzlouis/Projet_PPMD_BEA_2023-2024/blob/BDD/doc/documentation_dev_toolbox_v2.html)
  
Voici le [fichier](https://github.com/Steinmetzlouis/Projet_PPMD_BEA_2023-2024/blob/BDD/Dev/toolbox.py)

## toolbox_v2.py:
Script Python permettant la connexion à une base de données PostgreSQL et la création d'une nouvelle table dans une base de données existante à partir d'un fichier XML au format du SIA. Ce script est surtout utile pour mettre à jour une BDDG dans PostgreSQL. C'est ce dernier qu'il faut lancer tous les mois, à chaque publication d'un nouveau fichier XML par le SIA. La documentation développeur est disponible ici : [documentation_dévelopeur_toolbox_v2](https://github.com/Steinmetzlouis/Projet_PPMD_BEA_2023-2024/blob/BDD/doc/documentation_dev_toolbox_v2.html)
  
Voici le [fichier](https://github.com/Steinmetzlouis/Projet_PPMD_BEA_2023-2024/blob/BDD/Dev/toolbox_v2.py)

## script_dev.py:
Script python dans lequel on test des ajouts de fonctions qui, une fois fonctionnelles, sont déployées dans toolbox.py et tollbox_v2.py.
  
Voici le [fichier](https://github.com/Steinmetzlouis/Projet_PPMD_BEA_2023-2024/blob/BDD/Dev/script_dev.py)

## Jeu de données test .xml:
XML simplifié construit à partir de la donnée du 10/23 suivant le formalisme du SIA-xml. Ne contient que les classes:
* Territoires
* Espaces
* Parties
* Volumes
* NavFixs
  
Voici le [fichier](https://github.com/Steinmetzlouis/Projet_PPMD_BEA_2023-2024/blob/BDD/Dev/donnees_test_v2.xml)


## Jeu de données test .csv:
BDDG simplifiée construit à partir de la donnée du 10/23 suivant le formalisme du SIA-xml. Format CSV, donc version non finale
  
Voici le [fichier](https://github.com/Steinmetzlouis/Projet_PPMD_BEA_2023-2024/blob/BDD/doc/ExBDDG.xlsx)
