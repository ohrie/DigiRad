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
from qgis.core import QgsMapLayerProxyModel, QgsFieldProxyModel, QgsMessageLog, QgsPointXY

from .qtHelpers import QtHelper
from .dialogstate import DialogStateMachine, DialogState
from .classes.layers.centerLayer import CenterLayer
from .classes.network import LevelOfCentrality
from .classes.layers.directRouteNetworkLayer import DirectRouteNetworklayer
from .classes.processing.directRouteNetwork import DirectRouteNetwork, DirectRouteGenerateMethod
from .classes.layers.routeNetworkLayer import RouteNetworklayer
from .classes.layers.analysisLayers import SupplyNetworkElementLayer, SupplyAggregatedNetworkElementLayer, BreakingPointsNetworkLayer
from .classes.processing.routeNetworkTask import RouteNetworkTask, RouteNetworkTaskResult
from .classes.processing.routeNetworkAnalyser import RouteNetworkAnalyser
from .classes.interaction.centerEdit import CenterEditFeatureHandler, CenterEditToolType
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

        LAYER_MANAGER.setContextRef(self.stateMachine.context)

        self.setupConnections()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
    
    def postSetupUi(self):
        # self.centersMapLayerSelection.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.reprojectSelectLayer.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.reprojectDemandSelectLayer.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.reprojectDemandSelectField.setFilters(QgsFieldProxyModel.Filter.Numeric)

        self.tabs = {
            DialogState.WELCOME: self.welcomeTab,
            DialogState.LCOATIONSELECT: self.locationTab,
            DialogState.CENTERPOINTS: self.centerTab,
            DialogState.CENTERPOINTSEDIT: self.centerEditTab,
            DialogState.AIRLINE: self.airlineTab,
            DialogState.REPROJECT: self.reprojectTab,
            DialogState.REPROJECTDEMAND: self.reprojectDemandTab,
        }

        self.centerEditTool = None
    
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

        self.centerEditAddutton.clicked.connect(self.onCenterEditAddutton)
        self.centerEditPropertiesButton.clicked.connect(self.onCenterEditPropertiesButton)
        self.centerEditGeometryButton.clicked.connect(self.onCenterEditGeometryButton)
        self.centerEditDeleteButton.clicked.connect(self.onCenterEditDeleteButton)

        # Airline page
        self.airlineBackButton.clicked.connect(self.onAirlineBackButton)
        self.airlineContinueButton.clicked.connect(self.onAirlineContinueButton)
        self.airlineGenerateButton.clicked.connect(self.onAirlineGenerateButton)

        # Route page
        self.reprojectBackButton.clicked.connect(self.onReprojectBackButton)
        self.reprojectContinueButton.clicked.connect(self.onReprojectContinueButton)
        self.reprojectGenerateButton.clicked.connect(self.onReprojectGenerateButton)
        self.reprojectCancelGenerateButton.clicked.connect(self.onReprojectCancelGenerateButton)
        self.reprojectDetourToleranceCheckbox.clicked.connect(self.onReprojectDetourToleranceCheckbox)

        # Reproject demand page
        self.reprojectDemandBackButton.clicked.connect(self.onReprojectDemandBackButton)
        self.reprojectDemandContinueButton.clicked.connect(self.onReprojectDemandContinueButton)
        self.reprojectDemandGenerateButton.clicked.connect(self.onReprojectDemandGenerateButton)
        self.reprojectDemandCancelGenerateButton.clicked.connect(self.onReprojectDemandCancelGenerateButton)
        self.reprojectDemandSelectLayer.layerChanged.connect(self.onReprojectDemandSelectLayerChanged)
    
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
        centerLayer = DialogState.CENTERPOINTS.value.getCenterLayer()

        if not centerLayer:
            if DialogState.CENTERPOINTS.value.getGenerateMethod() == DirectRouteGenerateMethod.MANUEL:
                centerLayer = CenterLayer.createEmpty(DialogState.CENTERPOINTS.value.getLOCS())
                DialogState.CENTERPOINTS.value.setCenterLayer(centerLayer)
                LAYER_MANAGER.update()
            else:
                return

        centerLayer.qgsLayer().startEditing()
        self.iface.setActiveLayer(centerLayer.qgsLayer())

        self.centerEditTool = CenterEditFeatureHandler(self.iface, centerLayer.qgsLayer())

        self.selectTab(DialogState.CENTERPOINTSEDIT)
    
    def showAirlinePage(self):
        self.airlineContinueButton.setEnabled(DialogState.AIRLINE.value.hasDirectRouteLayer())
        self.selectTab(DialogState.AIRLINE)
    
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
            self.reprojectContinueButton.setEnabled(True)

        self.selectTab(DialogState.REPROJECT)
    
    def showReprojectDemandPage(self):
        if DialogState.REPROJECTDEMAND.value.isProcessing():
            self.reprojectDemandGenerateButton.hide()
            self.reprojectDemandProgressBar.show()
            self.reprojectDemandCancelGenerateButton.show()
            self.reprojectDemandBackButton.setEnabled(False)
            self.reprojectDemandContinueButton.setEnabled(False)
            self.reprojectDemandProgressBar.setValue(DialogState.REPROJECTDEMAND.value.getProgress())
        else:
            self.reprojectDemandGenerateButton.show()
            self.reprojectDemandProgressBar.hide()
            self.reprojectDemandCancelGenerateButton.hide()
            self.reprojectDemandBackButton.setEnabled(True)
            self.reprojectDemandContinueButton.setEnabled(False)

            if not self.reprojectDemandSelectLayer.currentLayer():
                networkLayer = self.reprojectSelectLayer.currentLayer()
                if networkLayer:
                    self.reprojectDemandSelectLayer.setLayer(networkLayer)

        self.selectTab(DialogState.REPROJECTDEMAND)

    ### SIGNALS

    ## HELPERS

    def guardLayerRegeneration(self, state: DialogState) -> bool:
        if DialogState.getValuesAfterContext(state, "LayerKeys"):
            return not QtHelper.askForLayerDeletion()
        return False

    ## WELCOME PAGE
    def onWelcomeNextButton(self):
        self.stateMachine.transitionTo(DialogState.LCOATIONSELECT)
    
    ## LOCATION PAGE
    def onLocationBackButton(self):
        self.stateMachine.transitionTo(DialogState.WELCOME)

    def onLocationCreateProject(self):
        self.setupMapView()
        self.stateMachine.transitionTo(DialogState.CENTERPOINTS)
    
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

    # HELPERS
    def centerUpdateContextLocsFromUi(self):
        locs = []
        if self.centerLOC2Check.isChecked():
            locs.append(LevelOfCentrality.II)
        if self.centerLOC3Check.isChecked():
            locs.append(LevelOfCentrality.III)
        if self.centerLOC4Check.isChecked():
            locs.append(LevelOfCentrality.IV)
        if self.centerLOCSingleCheck.isChecked():
            locs.append(LevelOfCentrality.Singular)
        
        DialogState.CENTERPOINTS.value.setLOCs(locs)

    # SIGNALS
    def onCentralBackButton(self):
        self.stateMachine.transitionTo(DialogState.LCOATIONSELECT)

    def onCentralNextButton(self):
        self.centerUpdateContextLocsFromUi()
        self.stateMachine.transitionTo(DialogState.CENTERPOINTSEDIT)

    def onCentralGenerateButton(self):
        # TODO: Replace with non dummy center values
        if self.guardLayerRegeneration(DialogState.CENTERPOINTS):
            return
        
        self.centerUpdateContextLocsFromUi()

        centerLayer = CenterLayer.loadFromFile(DUMMY_CENTER_OGR_PATH, DialogState.CENTERPOINTS.value.getLOCS())
        if centerLayer:
            DialogState.CENTERPOINTS.value.setCenterLayer(centerLayer)
            LAYER_MANAGER.update()
            self.showCenterPointsPage()

    def onCenterAutoRadioButton(self):
        DialogState.CENTERPOINTS.value.setGenerateMethod(DirectRouteGenerateMethod.AUTO)
        self.showCenterPointsPage()

    def onCenterManualRadioButton(self):
        DialogState.CENTERPOINTS.value.setGenerateMethod(DirectRouteGenerateMethod.MANUEL)
        self.showCenterPointsPage()
    
    ## CENTER EDIT PAGE

    # HELPERS
    def onCenterEditLeave(self):
        self.centerEditTool.restore()

        centerLayer = DialogState.CENTERPOINTS.value.getCenterLayer()
        if not centerLayer:
            return
        
        editBuffer = centerLayer.qgsLayer().editBuffer()
        if not editBuffer:
            return
        
        if editBuffer.isModified():
            if self.guardLayerRegeneration(DialogState.CENTERPOINTS):
                centerLayer.qgsLayer().rollBack()
                return
            else:
                centerLayer.qgsLayer().commitChanges()
                centerLayer.update()
                DialogState.CENTERPOINTS.value.setCenterLayer(centerLayer)
                LAYER_MANAGER.update()
        else:
            centerLayer.qgsLayer().commitChanges()
    
    # SIGNALS
    def onCenterEditBackButton(self):
        self.onCenterEditLeave()
        self.stateMachine.transitionTo(DialogState.CENTERPOINTS)
    
    def onCenterEditContinueButton(self):
        self.onCenterEditLeave()
        self.stateMachine.transitionTo(DialogState.AIRLINE)
    
    def onCenterEditAddutton(self):
        if self.centerEditTool:
            self.centerEditTool.setTool(CenterEditToolType.AddFeature)

    def onCenterEditPropertiesButton(self):
        if self.centerEditTool:
            self.centerEditTool.setTool(CenterEditToolType.PropertyEdit)

    def onCenterEditGeometryButton(self):
        if self.centerEditTool:
            self.centerEditTool.setTool(CenterEditToolType.MoveGeometry)

    def onCenterEditDeleteButton(self):
        if self.centerEditTool:
            self.centerEditTool.setTool(CenterEditToolType.DeleteFeature)

    ## AIRLINE PAGE
    def onAirlineBackButton(self):
        self.stateMachine.transitionTo(DialogState.CENTERPOINTSEDIT)
    
    def onAirlineContinueButton(self):
        self.stateMachine.transitionTo(DialogState.REPROJECT)

    def onAirlineGenerateButton(self):
        if self.guardLayerRegeneration(DialogState.AIRLINE):
            return
        
        centerLayer = DialogState.CENTERPOINTS.value.getCenterLayer()

        if not centerLayer:
            return
        
        drn = DirectRouteNetwork(centerLayer)
        routeEntries = drn.createNetwork()
        directRouteLayer = DirectRouteNetworklayer(routeEntries)
        if directRouteLayer:
            DialogState.AIRLINE.value.setDirectRouteLayer(directRouteLayer)
            LAYER_MANAGER.update()
            self.showAirlinePage()

    # REPROJECT PAGE
    def onReprojectBackButton(self):
        self.stateMachine.transitionTo(DialogState.AIRLINE)

    def onReprojectContinueButton(self):
        self.stateMachine.transitionTo(DialogState.REPROJECTDEMAND)

    def onReprojectGenerateButton(self):
        if self.guardLayerRegeneration(DialogState.REPROJECT):
            return
        
        directRouteLayer = DialogState.AIRLINE.value.getDirectRouteLayer()

        if not directRouteLayer:
            return
        networkLayer = self.reprojectSelectLayer.currentLayer()
        if not networkLayer:
            return
        
        DialogState.REPROJECT.value.setNetworklayer(networkLayer)

        if self.reprojectDetourToleranceCheckbox.isChecked():
            DialogState.REPROJECT.value.setDetourTolerance(self.reprojectDetourToleranceSpinbox.value() / 100.0)
        else:
            DialogState.REPROJECT.value.setDetourTolerance(0.0)

        task = RouteNetworkTask.createAndRunFromContextStateHandler(DialogState.context(), self.onReprojectGenerateResult, self.onReprojectGenerateProgressChanged)
        # Save the task into the context, so it does not get garbage collected
        DialogState.REPROJECT.value.setProcessing(task)
        self.showReprojectPage()
    
    def onReprojectGenerateResult(self, result: Tuple[bool, RouteNetworkTaskResult]):
        sucees, taskResult = result

        DialogState.REPROJECT.value.setProcessing(None)

        self.showReprojectPage()

        if sucees:
            routeLayer = RouteNetworklayer(taskResult.routeEntries)
            DialogState.REPROJECT.value.setRouteLayer(routeLayer)
            DialogState.REPROJECT.value.setPathfinder(taskResult.pathFinder)
            networkAnalyser = RouteNetworkAnalyser(taskResult.pathFinder.graph, routeLayer.routeEntries, routeLayer.config)
            networkElements = networkAnalyser.createNetworkElements()
            (aggregatedElements, breakingPoints) = networkAnalyser.aggregateElements(networkElements)
            supplyNetworkLayer = SupplyNetworkElementLayer(networkElements)
            supplyAggregatedNetworkLayer = SupplyAggregatedNetworkElementLayer(aggregatedElements)
            breakingPointsNetworkLayer = BreakingPointsNetworkLayer(breakingPoints)
            DialogState.REPROJECT.value.setSupplyNetworkLayer(supplyNetworkLayer)
            DialogState.REPROJECT.value.setAggregatedSupplyNetworkLayer(supplyAggregatedNetworkLayer)
            DialogState.REPROJECT.value.setBreakingPointsNetworkLayer(breakingPointsNetworkLayer)
            LAYER_MANAGER.update()
        else:
            QgsMessageLog.logMessage(f"Error while processing: {taskResult}")
    
    def onReprojectGenerateProgressChanged(self, progress):
        oldValue = DialogState.REPROJECT.value.setProgress(int(progress))
        if oldValue != progress:
            self.showReprojectPage()
    
    def onReprojectCancelGenerateButton(self):
        task = DialogState.REPROJECT.value.getProcessing()
        if task:
            task.cancel()
    
    def onReprojectDetourToleranceCheckbox(self):
        self.reprojectDetourToleranceSpinbox.setEnabled(self.reprojectDetourToleranceCheckbox.isChecked())

    
    # REPROJECT DEMAND PAGE
    def onReprojectDemandBackButton(self):
        self.stateMachine.transitionTo(DialogState.REPROJECT)

    def onReprojectDemandContinueButton(self):
        pass

    def onReprojectDemandGenerateButton(self):
        if self.guardLayerRegeneration(DialogState.REPROJECTDEMAND):
            return
        
        directRouteLayer = DialogState.AIRLINE.value.getDirectRouteLayer()

        if not directRouteLayer:
            return
        networkLayer = self.reprojectDemandSelectLayer.currentLayer()
        if not networkLayer:
            return
        
        DialogState.REPROJECTDEMAND.value.setNetworklayer(networkLayer)


        task = RouteNetworkTask.createAndRunFromContextStateHandler(DialogState.context(), self.onReprojectDemandGenerateResult, self.onReprojectDemandGenerateProgressChanged)
        # Save the task into the context, so it does not get garbage collected
        DialogState.REPROJECTDEMAND.value.setProcessing(task)
        self.showReprojectPage()
    
    def onReprojectDemandSelectLayerChanged(self):
        networkLayer = self.reprojectDemandSelectLayer.currentLayer()
        if not networkLayer:
            return
        
        self.reprojectDemandSelectField.setLayer(networkLayer)
    
    def onReprojectDemandGenerateResult(self, result: Tuple[bool, RouteNetworkTaskResult]):
        sucees, taskResult = result

        DialogState.REPROJECTDEMAND.value.setProcessing(None)

        self.showReprojectPage()

        if sucees:
            routeLayer = RouteNetworklayer(taskResult.routeEntries)
            DialogState.REPROJECTDEMAND.value.setRouteLayer(routeLayer)
            DialogState.REPROJECTDEMAND.value.setPathfinder(taskResult.pathFinder)
            networkAnalyser = RouteNetworkAnalyser(taskResult.pathFinder.graph, routeLayer.routeEntries, routeLayer.config)
            networkElements = networkAnalyser.createNetworkElements()
            (aggregatedElements, breakingPoints) = networkAnalyser.aggregateElements(networkElements)
            supplyNetworkLayer = SupplyNetworkElementLayer(networkElements)
            supplyAggregatedNetworkLayer = SupplyAggregatedNetworkElementLayer(aggregatedElements)
            breakingPointsNetworkLayer = BreakingPointsNetworkLayer(breakingPoints)
            DialogState.REPROJECTDEMAND.value.setSupplyNetworkLayer(supplyNetworkLayer)
            DialogState.REPROJECTDEMAND.value.setAggregatedSupplyNetworkLayer(supplyAggregatedNetworkLayer)
            DialogState.REPROJECTDEMAND.value.setBreakingPointsNetworkLayer(breakingPointsNetworkLayer)
            LAYER_MANAGER.update()
        else:
            QgsMessageLog.logMessage(f"Error while processing: {taskResult}")
    
    def onReprojectDemandGenerateProgressChanged(self, progress):
        oldValue = DialogState.REPROJECTDEMAND.value.setProgress(int(progress))
        if oldValue != progress:
            self.showReprojectDemandPage()
    
    def onReprojectDemandCancelGenerateButton(self):
        task = DialogState.REPROJECTDEMAND.value.getProcessing()
        if task:
            task.cancel()
    
    