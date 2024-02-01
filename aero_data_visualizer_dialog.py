# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AeroDataVisualizerDialog
                                 A QGIS plugin
 This plugin allows to visualize aeronautical data
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-01-08
        git sha              : $Format:%H$
        copyright            : (C) 2024 by BEA
        email                : louise.redlinger@ensg.eu
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import os.path as op

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject, QgsGeometry, QgsMessageLog, Qgis,\
    QgsExpressionContextUtils
from qgis.PyQt.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout
from qgis.core import QgsVectorLayer, QgsDataSourceUri, QgsProject, QgsWkbTypes

# Librairie saisie d'emprise (TRI A FAIRE!)
from qgis.core import QgsRectangle
from qgis.core import QgsPointXY
from qgis.PyQt.QtWidgets import QApplication, QMessageBox
from qgis.gui import QgsMapTool, QgsMapToolExtent, QgsRubberBand, QgsMapCanvas

from PyQt5.QtCore import Qt
import json
from qgis.core import QgsVectorLayer, QgsDataSourceUri, QgsProject, QgsWkbTypes

#dates
from datetime import datetime
from qgis.core import QgsDataSourceUri, QgsProject

from .mytoolbox import nearest_table_date, msg_box, import_pkg_mod

import_pkg_mod("psycopg2")
import psycopg2
# import_pkg_mod("SQLAlchemy")
# import_pkg_mod("GeoAlchemy2")

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'aero_data_visualizer_dialog_base.ui'))


# JSON_LOG_FILE = "id.json"
JSON_LOG_FILE = "jfv.json"
SCHEMA = "public"
GEOM_COL = "geometry"
STYLES = {QgsWkbTypes.Point : "style_point_sia.qml", QgsWkbTypes.Polygon: "style_polygon_sia.qml"}


class AeroDataVisualizerDialog(QtWidgets.QDialog, FORM_CLASS):
    
    def __init__(self, iface, parent=None):
        """
        Initialise une instance de la classe AeroDataVisualizerDialog.

        Args:
            iface (QgisInterface): Interface QGIS permettant l'accès aux fonctionnalités de QGIS.
            parent (QWidget): Widget parent de la fenêtre de dialogue (par défaut : None).
        """
        super(AeroDataVisualizerDialog, self).__init__(parent)

        # Assignation de l'interface QGIS
        self.iface = iface

        # Configuration de l'interface utilisateur
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)

        # Initialisation des variables de classe
        self.rubberband = None
        self.mapTool = None
        self.extent = None
        self.extent_wgs84 = None
        self.date = None
        self.fields = None
        self.sql_query = None
        self.cursor = None

        # Chemin du répertoire du plugin
        self.plugin_dir = op.dirname(__file__)

        self.confirmButton.clicked.connect(self.on_valider_clicked)
        self.coverageButton.clicked.connect(self.on_saisir_emprise_clicked)

        # Connecter le clic sur le bouton de visualisation à la méthode correspondante
        self.selectAllButton.clicked.connect(self.on_select_all_clicked)
        self.lineEdit.editingFinished.connect(lambda: self.update_table(self.cursor, user_filter=self.lineEdit.text()))
        self.visualizeButton.clicked.connect(self.on_visualiser_clicked)


    def handle_extent_selected(self):
        """
        Gère la sélection de l'étendue sur la carte QGIS par l'utilisateur. 
        
        Elle récupère l'étendue sélectionnée par l'utilisateur, s'assure que ces informations 
        soient dans le système de coordonnées WGS84, et affiche les coordonnées du coin inférieur 
        gauche et supérieur droit  de l'emprise correspondante dans une étiquette visible depuis l'interface. 
        
        De plus, elle met à jour une prévisualisation de la carte en affichant l'étendue sélectionnée dans l'interface.

        """
        # Récupérer l'étendue sélectionnée par l'utilisateur
        self.extent = self.mapTool.extent()

        # Définir le système de référence source (le CRS actuel de la carte)
        source_crs = self.iface.mapCanvas().mapSettings().destinationCrs()

        # Définir le système de référence cible (WGS84)
        target_crs = QgsCoordinateReferenceSystem('EPSG:4326')  # EPSG:4326 est le code EPSG pour WGS84

        # Créer l'objet de transformation des coordonnées
        transform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())

        # Appliquer la transformation aux coins de l'emprise
        self.extent_wgs84 = transform.transformBoundingBox(self.extent, QgsCoordinateTransform.ForwardTransform)
        extent_wgs84_str = 'xmin: {:.2f}, ymin: {:.2f}, xmax: {:.2f}, ymax: {:.2f}'.format(
            round(self.extent_wgs84.xMinimum(), 2),
            round(self.extent_wgs84.yMinimum(), 2),
            round(self.extent_wgs84.xMaximum(), 2),
            round(self.extent_wgs84.yMaximum(), 2)
        )

        # Afficher l'étendue sélectionnée dans les coordonnées WGS84
        QgsMessageLog.logMessage(f"Emprise sélectionnée (WGS84): {extent_wgs84_str}", 'ADV', level=Qgis.Info)
        self.empriseLabel.setText(f'Emprise définie : {extent_wgs84_str}')

        # Effacer le rubberband et le redessiner avec la nouvelle étendue sélectionnée
        self.mapTool.clearRubberBand()
        self.mapCanvas.setLayers(self.iface.mapCanvas().layers())
        self.mapCanvas.setExtent(self.extent)
        self.mapCanvas.setCanvasColor(Qt.white)
        self.mapCanvas.enableAntiAliasing(True)
        if self.rubberband is not None:
            self.mapCanvas.scene().removeItem(self.rubberband)
        self.rubberband = QgsRubberBand(self.mapCanvas, QgsWkbTypes.PolygonGeometry)  # polygone
        self.rubberband.setToGeometry(QgsGeometry.fromRect(self.extent), None)
        self.mapCanvas.refreshAllLayers()
        self.mapCanvas.show()

        # Afficher la fenêtre normale
        self.showNormal()
        self.raise_()
        self.activateWindow()



    def on_valider_clicked(self):
        """
        Gère l'événement de clic sur le bouton "Valider".

        Cette méthode récupère la date saisie par l'utilisateur et effectue une requête
        à la base de données pour obtenir les dates de mise à jour de toutes les tables de la BDD
        pour ensuite déterminer quelle est la table avec la date de mise à jour la plus proche antièrieurement
        à celle saisie par l'utilisateur.
        En fonction de l'étendue spatiale sélectionnée, une requête SQL est construite
        pour extraire les identifiants 'lk' des objets dont la géométrie est comprise 
        dans l'enveloppe spatiale définie dans la base de données.
        Les identifiants 'lk' sont ensuite affichés dans un tableau dans le second onglet
        pour la sélection ultérieure par l'utilisateur.

        """
        # Désactiver l'outil de sélection d'emprise sur la carte
        self.iface.mapCanvas().unsetMapTool(self.mapTool)

        # Reset bouton select all
        self.selectAllButton.setText("Tout sélectionner")

        # Récupérer la date saisie par l'utilisateur
        if self.surveyDate:
            user_date = self.surveyDate.date().toPyDate()
            QgsMessageLog.logMessage(f"Date choisie : {user_date.isoformat()}", 'ADV', level=Qgis.Info)
        else:
            msg_box("ADV", "Choisir une date.", QMessageBox.Warning, self)
            return

        # Récupérer les paramètres de connexion à la base de données depuis un fichier JSON
        path = op.join(op.dirname(__file__), JSON_LOG_FILE)
        with open(path) as file:
            conn_params = json.load(file)

        # Établir une connexion à la base de données PostgreSQL
        conn = psycopg2.connect(**conn_params)
        self.cursor = conn.cursor()

        # Sélectionner les noms des tables commençant par "XML_SIA_"
        self.cursor.execute(f"SELECT table_name FROM information_schema.tables "
                       f"WHERE table_schema = '{SCHEMA}' AND table_name LIKE 'XML_SIA_%'")
        tables = [table[0] for table in self.cursor.fetchall()]

        # Formater les dates des tables pour une comparaison ultérieure
        dates_formatted = []
        for table in tables:
            date_part = table.replace("XML_SIA_", "")  
            try:
                date_obj = datetime.strptime(date_part, "%Y_%m_%d")
                dates_formatted.append(date_obj.date())
            except ValueError:
                QgsMessageLog.logMessage(f"Impossible de convertir la date dans le nom de la table : {table}", 'ADV', level=Qgis.Info)

        # Sélectionner la date la plus proche de celle saisie par l'utilisateur
        self.date = nearest_table_date(user_date, dates_formatted)
        if self.date is None:
            msg_box("ADV", f"Choisir une date ultérieure au {min(dates_formatted).isoformat()}", QMessageBox.Warning, self)
            return
        QgsMessageLog.logMessage(f"Date antérieure la plus proche dans la base : {self.date}", 'ADV', level=Qgis.Info)

        self.update_table(self.cursor)

        # Passer à l'onglet de sélection des attributs
        self.tabWidget.setCurrentIndex(1)


    def update_table(self, cursor, user_filter=None):
        """Update QTableWidget with SQL query built with extent, table name and optional user filter

        Args:
            cursor: psycopg2.extensions.cursor
            user_filter: str
        """
        if self.cursor is None:
            return
        # Construire la requête SQL en fonction de l'étendue spatiale sélectionnée
        if self.extent_wgs84 is not None:
            rect = self.extent_wgs84
            xmin, ymin, xmax, ymax = rect.xMinimum(), rect.yMinimum(), rect.xMaximum(), rect.yMaximum()
            geom_bound = f'ST_MakeEnvelope({xmin}, {ymin}, {xmax}, {ymax}, 4326)'
            spatial_query = "ST_Within" if self.within_button.isChecked() else "ST_Intersects"
            self.sql_query = f"""SELECT lk FROM {SCHEMA}."XML_SIA_{self.date}" WHERE {spatial_query}({GEOM_COL}, {geom_bound})"""
        else:
            self.sql_query = f"""SELECT lk FROM {SCHEMA}."XML_SIA_{self.date}" """

        if user_filter is not None:
            self.sql_query += " AND" if "WHERE" in self.sql_query else "WHERE" + f" UPPER(lk) LIKE UPPER('%{user_filter}%')"

                # Exécuter la requête SQL pour récupérer les identifiants 'lk'
        QgsMessageLog.logMessage(f"Requête : {self.sql_query}", 'ADV', level=Qgis.Info)
        self.cursor.execute(self.sql_query)
        lk_names = self.cursor.fetchall()

        # Afficher les identifiants 'lk' dans un tableau pour la sélection ultérieure par l'utilisateur
        self.fields = []
        for name in lk_names:
            self.fields.append(name[0])

        # Créer un nouveau tableau pour afficher les identifiants 'lk'
        self.tableWidget.setRowCount(len(self.fields))
        self.tableWidget.setColumnCount(2)
        header = self.tableWidget.horizontalHeader()
        header.setStretchLastSection(True)
        self.tableWidget.setHorizontalHeaderLabels(["", "Nom attribut"])
        for i, field_name in enumerate(self.fields):
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Unchecked)
            self.tableWidget.setItem(i, 0, item)
            self.tableWidget.setItem(i, 1, QTableWidgetItem(field_name))

        # Configurer l'affichage du nouveau tableau et le bouton de visualisation
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)


    def on_visualiser_clicked(self):
        """
        Gère l'événement de clic sur le bouton "Visualiser".

        Cette méthode récupère les champs sélectionnés par l'utilisateur, puis crée
        des couches vectorielles dans QGIS à partir des données correspondantes dans la base de données.
        Les couches sont organisées dans un groupe de couches portant le nom de la table de la BDD dont elles sont issues.

        """
        # Récupérer les champs sélectionnés par l'utilisateur
        liste = self.get_fields()
        if len(liste) == 0:
            return

        # Enregistrer les champs sélectionnés dans le journal de messages
        QgsMessageLog.logMessage(f"Liste points = {liste}", 'ADV', level=Qgis.Info)

        # Nom de la table XML_SIA correspondante à la date sélectionnée par l'utilisateur
        table = f"XML_SIA_{self.date}"

        # Types de géométrie à prendre en charge (point, ligne, polygone)
        geometries = [QgsWkbTypes.Point, QgsWkbTypes.LineString, QgsWkbTypes.Polygon]

        # Construction de la clause WHERE pour la requête SQL
        where_sql = f'lk IN {str(tuple(liste)).replace(",","") if len(liste) < 2 else str(tuple(liste))}'

        # Chemin vers le fichier contenant les informations de connexion
        path = op.join(op.dirname(__file__), JSON_LOG_FILE)

        # Définir le chemin d'accès pour les symboles SIA
        QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(), "svg_path",
                                                     op.join(self.plugin_dir, "symboles_sia/"))

        # Charger les informations de connexion à la base de données depuis le fichier JSON
        with open(path) as file:
            conn = json.load(file)
            groupName = table

            # Création d'un groupe de couches nommé "XML_SIA_AAAA-MM-JJ"
            root = QgsProject.instance().layerTreeRoot()
            group = root.insertGroup(0, groupName)

            # Création des couches vectorielles pour chaque type de géométrie
            for geom in geometries:
                uri = QgsDataSourceUri()
                uri.setConnection(conn["host"], conn["port"], conn["database"], conn["user"], conn["password"])
                uri.setSrid("4326")
                uri.setWkbType(geom)
                uri.setDataSource(SCHEMA, table, GEOM_COL, aKeyColumn='pk', aSql=where_sql)

                # Nom de la couche : "XML_SIA_AAAA-MM-JJ_GeometryType"
                layer = QgsVectorLayer(uri.uri(), f"{table}_{QgsWkbTypes.displayString(geom)}", "postgres")

                # Ajout de la couche au groupe
                group.addLayer(layer)
                QgsProject.instance().addMapLayer(layer, False)

                # Chargement du style de la couche (s'il est disponible)
                if geom in STYLES:
                    layer.loadNamedStyle(op.join(self.plugin_dir, STYLES[geom]))

                # Actualisation de la couche
                layer.triggerRepaint()


    def on_select_all_clicked(self):
        reversed_text = {"Tout sélectionner": "Tout désélectionner", "Tout désélectionner": "Tout sélectionner"}
        bool_text = {"Tout sélectionner": 2, "Tout désélectionner": 0} # Qt.Checked = 2
        text = self.selectAllButton.text()
        for row in range(self.tableWidget.rowCount()):
            self.tableWidget.item(row, 0).setCheckState(bool_text[text])
        self.selectAllButton.setText(reversed_text[text])


    def get_fields(self):
        """
        Récupère les champs sélectionnés par l'utilisateur dans le tableau du second onglet.

        Cette méthode parcourt le tableau des attributs et récupère les champs
        qui ont été cochés par l'utilisateur. Elle retourne une liste contenant
        les noms des champs sélectionnés.

        Returns:
            list: Liste des noms des champs sélectionnés par l'utilisateur.
        """
        fields = []
        # Parcourir toutes les lignes du tableau
        for row in range(self.tableWidget.rowCount()):
            # Récupérer l'élément de case à cocher dans la colonne 0
            item = self.tableWidget.item(row, 0)
            # Vérifier si la case est cochée
            if item.checkState() == Qt.Checked:
                # Ajouter le nom du champ correspondant à la liste des champs sélectionnés
                fields.append(self.tableWidget.item(row, 1).text())
        return fields


    def on_saisir_emprise_clicked(self):
        """
        Gère l'événement de clic sur le bouton "Saisir l'emprise".

        Cette méthode cache la fenêtre du plugin et active l'outil de sélection d'emprise sur la carte.
        Lorsque l'utilisateur sélectionne une emprise sur la carte, la méthode handle_extent_selected est appelée.

        """
        # Cacher la fenêtre du plugin
        self.showMinimized()

        # Accéder à la carte QGIS
        canvas = self.iface.mapCanvas()

        # Activer l'outil de sélection d'emprise sur la carte
        self.mapTool = QgsMapToolExtent(canvas)
        self.mapTool.extentChanged.connect(self.handle_extent_selected)
        canvas.setMapTool(self.mapTool)
