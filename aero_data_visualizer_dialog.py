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

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject, QgsWkbTypes, QgsGeometry

# Librairie saisie d'emprise (TRI A FAIRE!)
from qgis.core import QgsRectangle
from qgis.core import QgsPointXY
from qgis.PyQt.QtWidgets import QApplication, QMessageBox
from qgis.gui import QgsMapTool, QgsMapToolExtent, QgsRubberBand, QgsMapCanvas

from PyQt5.QtCore import Qt

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'aero_data_visualizer_dialog_base.ui'))



class MapToolSelectExtent(QgsMapTool):
    def __init__(self, canvas, callback):
        super(MapToolSelectExtent, self).__init__(canvas)
        self.canvas = canvas
        self.callback = callback
        self.start_point = None

    def canvasPressEvent(self, event):
        # Enregistrer le point de départ de la sélection
        self.start_point = self.toMapCoordinates(event.pos())

    def canvasReleaseEvent(self, event):
        if self.start_point is None:
            return

        # Récupérer le point de fin de la sélection
        end_point = self.toMapCoordinates(event.pos())

        # Créer une emprise rectangulaire à partir des deux points
        extent = QgsRectangle(self.start_point, end_point)

        # Appeler la fonction callback avec l'emprise sélectionnée
        if callable(self.callback):
            self.callback(extent)

        # Réinitialiser le point de départ
        self.start_point = None


class SaisirEmpriseMapTool(QgsMapTool):
    def __init__(self, canvas):
        super(SaisirEmpriseMapTool, self).__init__(canvas)
        self.canvas = canvas
        self.emprise_defined = False
        self.emprise = QgsRectangle()

    def canvasPressEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        point = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)
        
        if not self.emprise_defined:
            self.emprise.set(QgsPointXY(point), QgsPointXY(point))
        else:
            self.emprise_defined = False
            self.emprise = QgsRectangle()

    def canvasMoveEvent(self, event):
        if not self.emprise_defined:
            x = event.pos().x()
            y = event.pos().y()
            point = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)
            self.emprise.set(QgsPointXY(self.emprise.xMinimum(), self.emprise.yMinimum()), QgsPointXY(point))

    def canvasReleaseEvent(self, event):
        if not self.emprise_defined:
            self.emprise_defined = True

    def is_emprise_defined(self):
        return self.emprise_defined

    def get_emprise(self):
        return self.emprise


class AeroDataVisualizerDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        """Constructor."""
        super(AeroDataVisualizerDialog, self).__init__(parent)
        self.iface = iface
        self.setupUi(self)

        print("Bienvenue dans le bien nommé plugin AeroDataVisualizer ! ")

        # self.mapCanvas.hide()
        self.rubberband = None

        # Pour trouver le QTabWidget 
        tab_widget = self.findChild(QtWidgets.QTabWidget, 'tabWidget')

        if tab_widget:
            
            print("TabWidget trouvé")

            # Pour trouver le premier onglet du TabWidget
            first_tab = tab_widget.widget(0)
            

            confirmButton = self.findChild(QtWidgets.QPushButton, 'confirmButton')
            coverageButton = self.findChild(QtWidgets.QPushButton, 'coverageButton')

            if confirmButton :

                print("Bouton 'Valider' trouvé")

                confirmButton.clicked.connect(self.on_valider_clicked)

            if coverageButton :

                print("Bouton 'Saisir emprise' trouvé")
                coverageButton.clicked.connect(self.on_saisir_emprise_clicked)

    def handle_extent_selected(self, maptool):
        extent = maptool.extent()

        # Définir le système de référence source (le CRS actuel de la carte)
        source_crs = self.iface.mapCanvas().mapSettings().destinationCrs()

        # Définir le système de référence cible (WGS84)
        target_crs = QgsCoordinateReferenceSystem('EPSG:4326')  # EPSG:4326 est le code EPSG pour WGS84

        # Créer l'objet de transformation des coordonnées
        transform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())

        # Appliquer la transformation aux coins de l'emprise
        extent_wgs84 = transform.transformBoundingBox(extent, QgsCoordinateTransform.ForwardTransform)
        extent_wgs84_str = 'xmin: {:.2f}, ymin: {:.2f}, xmax: {:.2f}, ymax: {:.2f}'.format(
            round(extent_wgs84.xMinimum(), 2),
            round(extent_wgs84.yMinimum(), 2),
            round(extent_wgs84.xMaximum(), 2),
            round(extent_wgs84.yMaximum(), 2)
        )

        print("Emprise sélectionnée (WGS84):", extent_wgs84_str)
        self.empriseLabel.setText(f'Emprise définie : {extent_wgs84_str}')

        maptool.clearRubberBand()

        self.mapCanvas.setLayers(self.iface.mapCanvas().layers())
        self.mapCanvas.setExtent(extent)
        self.mapCanvas.setCanvasColor(Qt.white)
        self.mapCanvas.enableAntiAliasing(True)
        if self.rubberband is not None:
            self.mapCanvas.scene().removeItem(self.rubberband)
        self.rubberband = QgsRubberBand(self.mapCanvas, QgsWkbTypes.PolygonGeometry)  # polygon
        self.rubberband.setToGeometry(QgsGeometry.fromRect(extent), None)
        self.mapCanvas.refreshAllLayers()
        self.mapCanvas.show()

        self.raise_()
        self.activateWindow()

    def on_valider_clicked(self):
        
        print('clic valider')

        # On cherche l'objet QDateEdit
        surveyDate = self.findChild(QtWidgets.QDateEdit, 'surveyDate')

        if surveyDate:
            # On récupère la valeur de la date saisie
            date_value = surveyDate.date().toString("yyyy-MM-dd")
            print("Date saisie :", date_value)
        else:
            print("Objet QDateEdit non trouvé.")
        
        tab_widget = self.findChild(QtWidgets.QTabWidget, 'tabWidget')
        tab_widget.setCurrentIndex(1)

    def on_saisir_emprise_clicked(self):

        # select_extent_tool = MapToolSelectExtent(self.iface.mapCanvas(), self.handle_extent_selected)
        # self.iface.mapCanvas().setMapTool(select_extent_tool)

        canvas = self.iface.mapCanvas()
        t = QgsMapToolExtent(canvas)
        t.extentChanged.connect(lambda: self.handle_extent_selected(t))
        canvas.setMapTool(t)

        # print('clic saisir emprise')
        #
        # # On crée et on active l'outil de carte personnalisé map_tool
        # map_tool = SaisirEmpriseMapTool(self.iface.mapCanvas())
        # self.iface.mapCanvas().setMapTool(map_tool)
        #
        # # Tant que l'utilisateur n'a pas saisi l'emprise, l'activité en cours continue
        # while not map_tool.is_emprise_defined():
        #     QApplication.processEvents()
        #
        # # On récupère l'emprise définie par l'utilisateur
        # emprise = map_tool.get_emprise()
        # print(f'Emprise définie: {emprise.toString()}')
        #
        # empriseLabel = self.findChild(QtWidgets.QLabel, 'empriseLabel')
        #
        # if empriseLabel :
        #
        #     print('empriseLabel trouvé')
        #     empriseLabel.setText(f'Emprise définie : {emprise.toString()}')
        #
        # else :
        #
        #     print('pas trouvé')
    

