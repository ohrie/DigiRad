# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DigiRadDialog
                                 A QGIS plugin
 Unterstützung bei der Erstellung von digitalen Angebotsnetzen für den Radverkehr
                             -------------------
        begin                : 2025-05-13
        git sha              : $Format:%H$
        copyright            : (C) 2025 by Vision Velo UG (haftungsbeschränkt)
        email                : info@vision-velo.de
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
from qgis.core import QgsMessageLog, QgsRasterLayer, QgsProject, QgsCoordinateReferenceSystem, QgsPointXY

from .classes.layers.centerLayer import CenterLayer
from .classes.layers.directRouteNetworkLayer import DirectRouteNetworklayer
from .statics import ARS_INDEX, PROCESSING_CONFIG, LAYER_MANAGER, DUMMY_CENTER_OGR_PATH

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'visionvelo_digirad_dialog_base.ui'))


class DigiRadDialog(QtWidgets.QWizard, FORM_CLASS):
    def __init__(self, iface, parent=None):
        """Constructor."""
        super(DigiRadDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.iface = iface
        self.setupUi(self)
        self.setupConnections()
    
    def setupConnections(self):
        # Connect signals and slots
        self.loadProjectButton.clicked.connect(self.onloadProjectButton)

        # Location page
        self.locationSearchButton.clicked.connect(self.onLocationSearchButton)
        self.locationResultsListWidget.currentItemChanged.connect(self.onLocationRegionItemChanged)

        # Center page
        self.centersGeneratePointsButton.clicked.connect(self.onCentersGeneratePointsButton)
    
    def setupMapView(self):
        # Setup map canvas
        canvas = self.iface.mapCanvas()
        # canvas.freeze(True)
        canvas.setDestinationCrs(LAYER_MANAGER.crs())
        canvas.setCenter(QgsPointXY(1528495,6630738))
        canvas.zoomScale(250000)
        # canvas.freeze(False)

        LAYER_MANAGER.show()

    
    ### SIGNALS
    
    def onloadProjectButton(self):
        self.setupMapView()
    
    ## LOCATION PAGE
    
    def onLocationSearchButton(self):
        results = ARS_INDEX.searchByName(self.locationLineEdit.text())

        self.locationResultsListWidget.clear()
        for (result, score) in results:
            self.locationResultsListWidget.addItem(result.name)
    
    def onLocationRegionItemChanged(self, item):
        if not item:
            return
        if PROCESSING_CONFIG.arsCode:
            if PROCESSING_CONFIG.arsCode.name == item.text():
                return

        self.locationSelectedRegionLabel.setText(item.text())
        code = ARS_INDEX.getARSCodeByName(item.text())
        if not code:
            return
        
        PROCESSING_CONFIG.setARSCode(code)
        LAYER_MANAGER.updateProjectName(PROCESSING_CONFIG.projectName)

        self.iface.mapCanvas().setCenter(code.center)
        self.iface.mapCanvas().refresh()

    ## CENTER PAGE

    def onCentersGeneratePointsButton(self):
        centerLayer = CenterLayer.loadFromFile(DUMMY_CENTER_OGR_PATH + "|layername=dresden_zentren", "Zentren")
        LAYER_MANAGER.updateCenterLayer(centerLayer)

        from .classes.processing.directRouteNetwork import DirectRouteNetwork

        drn = DirectRouteNetwork(centerLayer)
        routeEntries = drn.createNetwork()
        directRouteLayer = DirectRouteNetworklayer(routeEntries)
        LAYER_MANAGER.updateDirectRouteLayer(directRouteLayer)
        
        
