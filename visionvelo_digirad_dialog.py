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
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import QgsMapLayerProxyModel, QgsMessageLog, QgsProject, QgsPointXY

from .dialogstate import DialogStateMachine, DialogState
from .classes.layers.centerLayer import CenterLayer
from .classes.layers.directRouteNetworkLayer import DirectRouteNetworklayer
from .classes.processing.directRouteNetwork import DirectRouteNetwork
from .classes.layers.routeNetworkLayer import RouteNetworklayer
from .classes.processing.routeNetwork import RouteNetwork
from .statics import ARS_INDEX, PROCESSING_CONFIG, LAYER_MANAGER, DUMMY_CENTER_OGR_PATH

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'visionvelo_digirad_dockwidget.ui'))


class DigiRadDialog(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

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
        self.postSetupUi()
        
        self.stateMachine = DialogStateMachine(DialogState.WELCOME, self)

        self.setupConnections()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
    
    def postSetupUi(self):
        self.centersMapLayerSelection.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.reprojectSelectLayer.setFilters(QgsMapLayerProxyModel.LineLayer)

        self.tabs = {
            DialogState.WELCOME: self.welcomeTab,
            DialogState.LCOATIONSELECT: self.locationTab,
            DialogState.CENTERPOINTS: self.centerTab,
            DialogState.CENTERPOINTSEDIT: self.centerEditTab,
            DialogState.AIRLINE: self.airlineTab,
            DialogState.AIRLINEEDIT: self.airlineEditTab,
            DialogState.REPROJECT: self.reprojectTab,
        }
    
    def setupConnections(self):
        # Connect signals and slots

        # Welcome Page
        self.welcomeNextButton.clicked.connect(self.onWelcomeNextButton)

        # Location page
        self.locationBackButton.clicked.connect(self.onLocationBackButton)
        self.locationCreateProject.clicked.connect(self.onLocationCreateProject)
        self.locationSearchButton.clicked.connect(self.onLocationSearchButton)
        self.locationResultsListWidget.currentItemChanged.connect(self.onLocationRegionItemChanged)

        # Center page
        self.centralGenerateButton.clicked.connect(self.onCentralGenerateButton)
        self.centralNextButton.clicked.connect(self.onCentralNextButton)
        self.centralBackButton.clicked.connect(self.onCentralBackButton)

        # Center edit page
        self.centerEditBackButton.clicked.connect(self.onCenterEditBackButton)
        self.centerEditContinueButton.clicked.connect(self.onCenterEditContinueButton)

        # Airline page
        self.airlineBackButton.clicked.connect(self.onAirlineBackButton)
        self.airlineContinueButton.clicked.connect(self.onAirlineContinueButton)
        self.airlineGenerateButton.clicked.connect(self.onAirlineGenerateButton)

        # Airline edit page
        self.airlineEditBackButton.clicked.connect(self.onAirlineEditBackButton)
        self.airlineEditContinueButton.clicked.connect(self.onAirlineEditContinueButton)

        # Route page
        self.reprojectBackButton.clicked.connect(self.onReprojectBackButton)
        self.reprojectContinueButton.clicked.connect(self.onReprojectContinueButton)
        self.reprojectGenerateButton.clicked.connect(self.onReprojectGenerateButton)
    
    def setupMapView(self):
        # Setup map canvas
        canvas = self.iface.mapCanvas()
        # canvas.freeze(True)
        canvas.setDestinationCrs(LAYER_MANAGER.crs())
        canvas.setCenter(QgsPointXY(1528495,6630738))
        canvas.zoomScale(250000)
        # canvas.freeze(False)

        LAYER_MANAGER.show()
    
    def selectTab(self, state: DialogState):
        for (tabState, tab) in self.tabs.items():
            tab.setEnabled(tabState == state)
        
        if state in self.tabs:
            self.tabWidget.setCurrentWidget(self.tabs[state])
    
    ### STATE TRANSITIONS

    def showWelcomePage(self, context):
        self.selectTab(DialogState.WELCOME)
    
    def showLocationSelectPage(self, context):
        self.selectTab(DialogState.LCOATIONSELECT)

    def showCenterPointsPage(self, context):
        self.selectTab(DialogState.CENTERPOINTS)
    
    def showCenterPointsEditPage(self, context):
        self.selectTab(DialogState.CENTERPOINTSEDIT)
    
    def showAirlinePage(self, context):
        self.selectTab(DialogState.AIRLINE)
    
    def showAirlineEditPage(self, context):
        self.selectTab(DialogState.AIRLINEEDIT)
    
    def showReprojectPage(self, context):
        self.selectTab(DialogState.REPROJECT)

    ### SIGNALS

    ## WELCOME PAGE
    def onWelcomeNextButton(self):
        self.stateMachine.transitionTo(DialogState.LCOATIONSELECT)
    
    ## LOCATION PAGE
    def onLocationBackButton(self):
        self.stateMachine.transitionTo(DialogState.WELCOME)

    def onLocationCreateProject(self):
        self.setupMapView()
        self.stateMachine.transitionTo(DialogState.CENTERPOINTS)
    
    def onCentralNextButton(self):
        self.stateMachine.transitionTo(DialogState.CENTERPOINTSEDIT)
    
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

        self.locationCreateProject.setEnabled(True)

        self.iface.mapCanvas().setCenter(code.center)
        self.iface.mapCanvas().refresh()

    ## CENTER PAGE
    def onCentralBackButton(self):
        self.stateMachine.transitionTo(DialogState.LCOATIONSELECT)

    def onCentralNextButton(self):
        self.stateMachine.transitionTo(DialogState.CENTERPOINTSEDIT)

    def onCentralGenerateButton(self):
        centerLayer = CenterLayer.loadFromFile(DUMMY_CENTER_OGR_PATH + "|layername=dresden_zentren", "Zentren")
        if centerLayer:
            LAYER_MANAGER.updateCenterLayer(centerLayer)
            self.centralNextButton.setEnabled(True)
    
    ## CENTER EDIT PAGE
    def onCenterEditBackButton(self):
        self.stateMachine.transitionTo(DialogState.CENTERPOINTS)
    
    def onCenterEditContinueButton(self):
        self.stateMachine.transitionTo(DialogState.AIRLINE)

    ## AIRLINE PAGE
    def onAirlineBackButton(self):
        self.stateMachine.transitionTo(DialogState.CENTERPOINTSEDIT)
    
    def onAirlineContinueButton(self):
        self.stateMachine.transitionTo(DialogState.AIRLINEEDIT)

    def onAirlineGenerateButton(self):
        centerLayer = LAYER_MANAGER.centerLayer

        if not centerLayer:
            return
        
        drn = DirectRouteNetwork(centerLayer)
        routeEntries = drn.createNetwork()
        directRouteLayer = DirectRouteNetworklayer(routeEntries)
        if directRouteLayer:
            LAYER_MANAGER.updateDirectRouteLayer(directRouteLayer)
            self.airlineContinueButton.setEnabled(True)

    ## AIRLINE EDIT PAGE
    def onAirlineEditBackButton(self):
        self.stateMachine.transitionTo(DialogState.AIRLINE)

    def onAirlineEditContinueButton(self):
        self.stateMachine.transitionTo(DialogState.REPROJECT)

    # REPROJECT PAGE
    def onReprojectBackButton(self):
        self.stateMachine.transitionTo(DialogState.AIRLINEEDIT)

    def onReprojectContinueButton(self):
        pass

    def onReprojectGenerateButton(self):
        directRouteLayer = LAYER_MANAGER.directRouteLayer

        if not directRouteLayer:
            return
        networkLayer = QgsProject.instance().mapLayersByName("graph_dd_eskn — dresden_lokales_netz")[0]

        rn = RouteNetwork(networkLayer, directRouteLayer)
        routeEntries = rn.createNetwork()
        routeLayer = RouteNetworklayer(routeEntries)
        LAYER_MANAGER.updateRouteLayer(routeLayer)