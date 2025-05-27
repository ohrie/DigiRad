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

from typing import Tuple

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import QgsMapLayerProxyModel, QgsMessageLog, QgsProject, QgsPointXY

from .dialogstate import DialogStateMachine, DialogState
from .classes.layers.centerLayer import CenterLayer
from .classes.network import LevelOfCentrality, ConnectivityFunction
from .classes.layers.directRouteNetworkLayer import DirectRouteNetworklayer
from .classes.processing.directRouteNetwork import DirectRouteNetwork, DirectRouteGenerateMethod
from .classes.layers.routeNetworkLayer import RouteNetworklayer
from .classes.processing.routeNetwork import RouteNetwork
from .classes.processing.routeNetworkTask import RouteNetworkTask
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
        # self.centersMapLayerSelection.setFilters(QgsMapLayerProxyModel.PointLayer)
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

        self.centerAutoRadioButton.toggled.connect(self.onCenterAutoRadioButton)
        self.centerManualRadioButton.toggled.connect(self.onCenterManualRadioButton)

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
        self.reprojectCancelGenerateButton.clicked.connect(self.onReprojectCancelGenerateButton)
    
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
    def showWelcomePage(self):
        self.selectTab(DialogState.WELCOME)
    
    def showLocationSelectPage(self):
        self.selectTab(DialogState.LCOATIONSELECT)

    def showCenterPointsPage(self):
        if DialogState.CENTERPOINTS.value.getGenerateMethod() == DirectRouteGenerateMethod.AUTO:
            self.centralGenerateButton.show()
            self.centralLOCBox.show()
        else:
            self.centralGenerateButton.hide()
            self.centralLOCBox.hide()
        
        self.centralNextButton.setEnabled(self.centerManualRadioButton.isChecked() or DialogState.CENTERPOINTS.value.hasCenterLayer())
        self.selectTab(DialogState.CENTERPOINTS)
    
    def showCenterPointsEditPage(self):
        self.selectTab(DialogState.CENTERPOINTSEDIT)
    
    def showAirlinePage(self):
        QgsMessageLog.logMessage(f"{DialogState.CENTERPOINTS.value.getLOCS()}")
        if not DialogState.AIRLINE.value.hasCFs():
            locs = DialogState.CENTERPOINTS.value.getLOCS()
            cfs = list(map(lambda l: l.toConnectivityFunction(), locs))
            DialogState.AIRLINE.value.setCFs(cfs)
        else:
            cfs = DialogState.AIRLINE.value.getCFs()
        
        QgsMessageLog.logMessage(f"{cfs}")
        
        self.airlineVFS2Check.setChecked(ConnectivityFunction.VFS_2 in cfs)
        self.airlineVFS3Check.setChecked(ConnectivityFunction.VFS_3 in cfs)
        self.airlineVFS4Check.setChecked(ConnectivityFunction.VFS_4 in cfs)
        
        self.airlineVFS2Check.setEnabled(ConnectivityFunction.VFS_2 in cfs)
        self.airlineVFS3Check.setEnabled(ConnectivityFunction.VFS_3 in cfs)
        self.airlineVFS4Check.setEnabled(ConnectivityFunction.VFS_4 in cfs)

        self.selectTab(DialogState.AIRLINE)
    
    def showAirlineEditPage(self):
        self.selectTab(DialogState.AIRLINEEDIT)
    
    def showReprojectPage(self):
        if DialogState.REPROJECT.value.isProcessing():
            self.reprojectGenerateButton.hide()
            self.reprojectProgressBar.show()
            self.reprojectCancelGenerateButton.show()
            self.reprojectBackButton.setEnabled(False)
            self.reprojectContinueButton.setEnabled(False)
            self.reprojectProgressBar.setValue(DialogState.REPROJECT.value.getProgress())
        else:
            self.reprojectGenerateButton.show()
            self.reprojectProgressBar.hide()
            self.reprojectCancelGenerateButton.hide()
            self.reprojectBackButton.setEnabled(True)
            self.reprojectContinueButton.setEnabled(False)

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
        locs = []
        if self.centerLOC2Check.chekced():
            locs.append(LevelOfCentrality.II)
        if self.centerLOC3Check.chekced():
            locs.append(LevelOfCentrality.III)
        if self.centerLOC4Check.chekced():
            locs.append(LevelOfCentrality.IV)

        DialogState.CENTERPOINTS.value.setLOCs(locs)
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
            DialogState.CENTERPOINTS.value.setCenterLayer(centerLayer)
            self.centralNextButton.setEnabled(True)

    def onCenterAutoRadioButton(self):
        DialogState.CENTERPOINTS.value.setGenerateMethod(DirectRouteGenerateMethod.AUTO)
        self.showCenterPointsPage()

    def onCenterManualRadioButton(self):
        DialogState.CENTERPOINTS.value.setGenerateMethod(DirectRouteGenerateMethod.MANUEL)
        self.showCenterPointsPage()
    
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
        networkLayer = self.reprojectSelectLayer.currentLayer()
        if not networkLayer:
            return

        task = RouteNetworkTask.createAndRunTask(networkLayer, directRouteLayer, self.onReprojectGenerateResult, self.onReprojectGenerateProgressChanged)
        # Save the task into the context, so it does not get garbage collected
        DialogState.REPROJECT.value.setProcessing(task)
        self.showReprojectPage()
    
    def onReprojectGenerateResult(self, result: Tuple[bool, any]):
        sucees, result = result

        DialogState.REPROJECT.value.setProcessing(None)
        self.showReprojectPage()

        if sucees:
            routeLayer = RouteNetworklayer(result)
            LAYER_MANAGER.updateRouteLayer(routeLayer)
        else:
            QgsMessageLog.logMessage(f"Error while processing: {result}")
    
    def onReprojectGenerateProgressChanged(self, progress):
        oldValue = DialogState.REPROJECT.value.setProgress(int(progress))
        if oldValue != progress:
            self.showReprojectPage()
    
    def onReprojectCancelGenerateButton(self):
        task = DialogState.REPROJECT.value.getProcessing()
        if task:
            task.cancel()

        
    
    