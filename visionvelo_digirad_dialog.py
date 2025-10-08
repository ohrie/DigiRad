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
from qgis.core import QgsMapLayerProxyModel, QgsFieldProxyModel, QgsMessageLog, QgsVectorLayer

from .qtHelpers import QtHelper
from .dialogstate import DialogStateMachine, DialogState
from .classes.layers.centerLayer import CenterLayer
from .classes.layers.baseLayer import BaseLayerProvider
from .classes.ars import ARSCodeStr
from .classes.network import LevelOfCentrality
from .classes.layers.directRouteNetworkLayer import DirectRouteNetworklayer, MissingRoutesLayer
from .classes.processing.directRouteNetwork import DirectRouteNetwork, DirectRouteGenerateMethod
from .classes.layers.routeNetworkLayer import RouteNetworklayer
from .classes.layers.analysisLayers import SupplyAggregatedNetworkElementLayer, BreakingPointsNetworkLayer
from .classes.processing.routeNetworkTaskHelpers import RouteNetworkTaskResult, RouteNetworkTaskProgress
from .classes.interaction.centerEdit import CenterEditFeatureHandler, CenterEditToolType
from .constants import AUTO_CENTER_POINTS_PATH
from .statics import ARS_INDEX
from .classes.layerManager import LayerManager
from .classes.processing.task import RouteNetworkTask

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'visionvelo_digirad_dockwidget.ui'))


class DigiRadDialog(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, iface, layerManager: LayerManager, parent=None):
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
        self.layerManager = layerManager

        self.layerManager.setContextRef(self.stateMachine.context)

        self.setupConnections()

        self.stateMachine.transitionTo(DialogState.WELCOME)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
    
    def postSetupUi(self):
        self.loadProjectButton.hide()
        self.centerMapLayerComboBox.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.reprojectSelectLayer.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.reprojectDemandSelectLayer.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.reprojectDemandSelectField.setFilters(QgsFieldProxyModel.Filter.Numeric)

        self.locationBaseMapComboBox.addItems(BaseLayerProvider.getLayerNames())
        self.locationBaseMapComboBox.setCurrentIndex(0)

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
        self.locationLineEdit.textChanged.connect(self.onLocationLineEditTextChanged)
        self.locationResultsListWidget.currentItemChanged.connect(self.onLocationRegionItemChanged)

        # Center page
        self.centralSaveProjectButton.clicked.connect(self.onSaveProjectButton)
        self.centralGenerateButton.clicked.connect(self.onCentralGenerateButton)
        self.centralNextButton.clicked.connect(self.onCentralNextButton)
        self.centralRestartButton.clicked.connect(self.onRestartButton)
        self.centerMapLayerComboBox.layerChanged.connect(self.onCenterMapLayerComboBox)
        self.centerLoadLayerButton.clicked.connect(self.onCenterLoadLayerButton)

        self.centerAutoRadioButton.toggled.connect(self.onCenterAutoRadioButton)
        self.centerManualRadioButton.toggled.connect(self.onCenterManualRadioButton)
        self.centerLayerRadioButton.toggled.connect(self.onCenterLayerRadioButton)

        # Center edit page
        self.centerEditRestartButton.clicked.connect(self.onRestartButton)
        self.centerEditSaveProjectButton.clicked.connect(self.onSaveProjectButton)
        self.centerEditBackButton.clicked.connect(self.onCenterEditBackButton)
        self.centerEditContinueButton.clicked.connect(self.onCenterEditContinueButton)

        self.centerEditAddutton.clicked.connect(self.onCenterEditAddutton)
        self.centerEditPropertiesButton.clicked.connect(self.onCenterEditPropertiesButton)
        self.centerEditGeometryButton.clicked.connect(self.onCenterEditGeometryButton)
        self.centerEditDeleteButton.clicked.connect(self.onCenterEditDeleteButton)

        # Airline page
        self.airlineRestartButton.clicked.connect(self.onRestartButton)
        self.airlineSaveProjectButton.clicked.connect(self.onSaveProjectButton)
        self.airlineBackButton.clicked.connect(self.onAirlineBackButton)
        self.airlineContinueButton.clicked.connect(self.onAirlineContinueButton)
        self.airlineGenerateButton.clicked.connect(self.onAirlineGenerateButton)

        # Route page
        self.reprojectRestartButton.clicked.connect(self.onRestartButton)
        self.reprojectSaveProjectButton.clicked.connect(self.onSaveProjectButton)
        self.reprojectBackButton.clicked.connect(self.onReprojectBackButton)
        self.reprojectContinueButton.clicked.connect(self.onReprojectContinueButton)
        self.reprojectGenerateButton.clicked.connect(self.onReprojectGenerateButton)
        self.reprojectCancelGenerateButton.clicked.connect(self.onReprojectCancelGenerateButton)
        self.reprojectDetourToleranceCheckbox.clicked.connect(self.onReprojectDetourToleranceCheckbox)
        self.reprojectCenterDistanceLabel.linkActivated.connect(self.onReprojectDemandCenterDistanceLabel)

        # Reproject demand page
        self.reprojectDemandRestartButton.clicked.connect(self.onRestartButton)
        self.reprojectDemandSaveProjectButton.clicked.connect(self.onSaveProjectButton)
        self.reprojectDemandBackButton.clicked.connect(self.onReprojectDemandBackButton)
        self.reprojectDemandGenerateButton.clicked.connect(self.onReprojectDemandGenerateButton)
        self.reprojectDemandCancelGenerateButton.clicked.connect(self.onReprojectDemandCancelGenerateButton)
        self.reprojectDemandSelectLayer.layerChanged.connect(self.onReprojectDemandSelectLayerChanged)
        self.reprojectDemandDetourToleranceCheckbox.clicked.connect(self.onReprojectDemandDetourToleranceCheckbox)
        self.reprojectDemandCenterDistanceLabel.linkActivated.connect(self.onReprojectDemandCenterDistanceLabel)
    
    def setupMapView(self):
        # Setup map canvas
        canvas = self.iface.mapCanvas()
        canvas.freeze(True)
        canvas.setDestinationCrs(self.layerManager.crs())

        if self.layerManager.processingConfig.arsCode:
            self.layerManager.show(self.layerManager.processingConfig.arsCode.center)
        else:
            self.layerManager.show()
    
    def selectTab(self, state: DialogState):
        for (tabState, tab) in self.tabs.items():
            tab.setEnabled(tabState == state)
        
        if state in self.tabs:
            self.tabWidget.setCurrentWidget(self.tabs[state])

    ### STATE TRANSITIONS
    def showWelcomePage(self):
        self.selectTab(DialogState.WELCOME)
        self.welcomeNextButton.setFocus()
    
    def showLocationSelectPage(self):
        self.locationLineEdit.setText("")
        self.locationResultsListWidget.clear()
        self.locationSelectedRegionLabel.setText("")
        self.locationProjectNameEdit.setText("")
        self.locationCreateProject.setEnabled(False)
        self.selectTab(DialogState.LCOATIONSELECT)
        self.locationLineEdit.setFocus()

    def showCenterPointsPage(self):
        if DialogState.CENTERPOINTS.value.getGenerateMethod() == DirectRouteGenerateMethod.AUTO:
            self.centralGenerateButton.show()
            self.centralLOCBox.show()
            self.centerMapLayerBox.hide()
        elif DialogState.CENTERPOINTS.value.getGenerateMethod() == DirectRouteGenerateMethod.MANUEL:
            self.centralGenerateButton.hide()
            self.centralLOCBox.hide()
            self.centerMapLayerBox.hide()
        elif DialogState.CENTERPOINTS.value.getGenerateMethod() == DirectRouteGenerateMethod.LAYER:
            self.centralGenerateButton.hide()
            self.centralLOCBox.hide()
            self.centerMapLayerBox.show()
        
        self.centralNextButton.setEnabled(self.centerManualRadioButton.isChecked() or DialogState.CENTERPOINTS.value.hasCenterLayer())
        self.selectTab(DialogState.CENTERPOINTS)
        self.centralGenerateButton.setFocus()
    
    def showCenterPointsEditPage(self):
        centerLayer = DialogState.CENTERPOINTS.value.getCenterLayer()

        if not centerLayer:
            if DialogState.CENTERPOINTS.value.getGenerateMethod() == DirectRouteGenerateMethod.MANUEL:
                centerLayer = CenterLayer.createEmpty(self.layerManager.processingConfig.arsCode.code)
                DialogState.CENTERPOINTS.value.setCenterLayer(centerLayer)
                self.layerManager.update()
            else:
                return

        centerLayer.qgsLayer().startEditing()
        self.iface.setActiveLayer(centerLayer.qgsLayer())

        self.centerEditTool = CenterEditFeatureHandler(self.iface, centerLayer.qgsLayer())

        self.selectTab(DialogState.CENTERPOINTSEDIT)
        self.centerEditContinueButton.setFocus()
    
    def showAirlinePage(self):
        self.airlineContinueButton.setEnabled(DialogState.AIRLINE.value.hasDirectRouteLayer())
        self.selectTab(DialogState.AIRLINE)
        self.airlineGenerateButton.setFocus()
    
    def showReprojectPage(self):
        if DialogState.REPROJECT.value.isProcessing():
            self.reprojectGenerateButton.hide()
            self.reprojectProgressBar.show()
            self.reprojectProgressLabel.show()
            self.reprojectCancelGenerateButton.show()
            self.reprojectRestartButton.setEnabled(False)
            self.reprojectSaveProjectButton.setEnabled(False)
            self.reprojectBackButton.setEnabled(False)
            self.reprojectContinueButton.setEnabled(False)
            progressInfo = DialogState.REPROJECT.value.getProgress()
            self.reprojectProgressBar.setValue(progressInfo.progress)
            self.reprojectProgressLabel.setText(progressInfo.message)
        else:
            self.reprojectGenerateButton.show()
            self.reprojectProgressBar.hide()
            self.reprojectProgressLabel.hide()
            self.reprojectCancelGenerateButton.hide()
            self.reprojectRestartButton.setEnabled(True)
            self.reprojectSaveProjectButton.setEnabled(True)
            self.reprojectBackButton.setEnabled(True)
            self.reprojectContinueButton.setEnabled(DialogState.REPROJECT.value.hasRouteLayer())
            self.reprojectProgressBar.setValue(0)
            self.reprojectProgressLabel.setText("")

        self.selectTab(DialogState.REPROJECT)
    
    def showReprojectDemandPage(self):
        if DialogState.REPROJECTDEMAND.value.isProcessing():
            self.reprojectDemandGenerateButton.hide()
            self.reprojectDemandProgressBar.show()
            self.reprojectDemandProgressLabel.show()
            self.reprojectDemandRestartButton.setEnabled(False)
            self.reprojectDemandSaveProjectButton.setEnabled(False)
            self.reprojectDemandCancelGenerateButton.show()
            self.reprojectDemandBackButton.setEnabled(False)
            progressInfo = DialogState.REPROJECTDEMAND.value.getProgress()
            self.reprojectDemandProgressBar.setValue(progressInfo.progress)
            self.reprojectDemandProgressLabel.setText(progressInfo.message)
        else:
            self.reprojectDemandGenerateButton.show()
            self.reprojectDemandProgressBar.hide()
            self.reprojectDemandProgressLabel.hide()
            self.reprojectDemandCancelGenerateButton.hide()
            self.reprojectDemandRestartButton.setEnabled(True)
            self.reprojectDemandSaveProjectButton.setEnabled(DialogState.REPROJECTDEMAND.value.hasRouteLayer())
            self.reprojectDemandBackButton.setEnabled(True)
            self.reprojectDemandProgressBar.setValue(0)
            self.reprojectDemandProgressLabel.setText("")

            if not self.reprojectDemandSelectLayer.currentLayer():
                networkLayer = self.reprojectSelectLayer.currentLayer()
                if networkLayer:
                    self.reprojectDemandSelectLayer.setLayer(networkLayer)

        self.selectTab(DialogState.REPROJECTDEMAND)

    ### SIGNALS

    def show(self):
        super().show()
        self.layerManager.removeAll()
        self.stateMachine.transitionTo(DialogState.WELCOME)

    ## HELPERS

    def guardLayerRegeneration(self, state: DialogState) -> bool:
        if DialogState.getValuesAfterContext(state, "LayerKeys"):
            return not QtHelper.askForLayerDeletion()
        return False
    
    def guardLayerCrsMistmatch(self, layer: QgsVectorLayer) -> bool:
        layerCrs = layer.crs().authid()
        projectCrs = self.layerManager.crs().authid()
        if layerCrs != projectCrs:
            QtHelper.showInformationBox(
                self,
                "Referenzsystem",
                f"Das angegebene Referenzsystem ({layerCrs}) stimmt nicht mit dem Projektreferenzsystem ({projectCrs}) überein.\n\nBitte Transformieren Sie die Daten zuerst in das geforderte Referenzsystem. (Menüpunkt Vektor > Datenmanangement-Werkzeuge > Layer reprojizieren, Ziel-KBS: {projectCrs})")
            return True
        return False
    
    def onRestartButton(self):
        reply = QtHelper.askForProjectRestart()
        if reply == QtHelper.Yes:
            self.layerManager.removeAll()
            self.centerAutoRadioButton.setChecked(True)
            self.stateMachine.transitionTo(DialogState.LCOATIONSELECT)
        elif reply == QtHelper.KeepOldProject:
            self.layerManager.unlink()
            self.centerAutoRadioButton.setChecked(True)
            self.stateMachine.transitionTo(DialogState.LCOATIONSELECT)
    
    def onSaveProjectButton(self):
        directory = QtHelper.askForProjectToSaveDirectory(self)
        if directory:
            result = self.layerManager.saveProjectToDisk(directory)
            (success, msg) = result
            if success:
                if msg:
                    msg = f"\nWeitere Informationen: {msg}"
                QtHelper.showInformationBox(self, "Speichern des Projekt", f"Projekt wurde erfolgreich unter {directory} gespeichert.{msg}")
                if self.stateMachine.currentState == DialogState.REPROJECTDEMAND:
                    self.stateMachine.transitionTo(DialogState.WELCOME)
            else:
                QtHelper.showInformationBox(self, "Speichern des Projekt", f"Fehler beim Speichern des Projekts unter {directory}:\n{msg}")

    ## WELCOME PAGE
    def onWelcomeNextButton(self):
        self.stateMachine.transitionTo(DialogState.LCOATIONSELECT)
    
    ## LOCATION PAGE
    def onLocationBackButton(self):
        self.stateMachine.transitionTo(DialogState.WELCOME)

    def onLocationCreateProject(self):
        if self.layerManager.processingConfig.arsCode and self.layerManager.processingConfig.arsCode.code.isZ2():
            QtHelper.showInformationBox(self, "Oberzentrum/Landkreis ausgewählt", "Die Nutzung des Plugins ist für Mittel- und Grundzentren optimiert. Bei der Anwendung auf Pberzentren oder Landkreise können unter Umständen weniger präzise Ergebnisse auftreten.")
        
        lineEditText = self.locationProjectNameEdit.text().strip()
        if lineEditText:
            self.layerManager.processingConfig.projectName = lineEditText
            self.layerManager.updateProjectName()
        DialogState.LCOATIONSELECT.value.setBaseLayerStr(self.locationBaseMapComboBox.currentText())
        self.setupMapView()
        self.stateMachine.transitionTo(DialogState.CENTERPOINTS)
    
    def onLocationLineEditTextChanged(self):
        self.locationResultsListWidget.clear()

        results = ARS_INDEX.findNamesBySearchName(self.locationLineEdit.text())
        if results:
            for result in results:
                self.locationResultsListWidget.addItem(result)
        else:
            self.layerManager.processingConfig.setARSCode(None)
            self.locationCreateProject.setEnabled(False)
            self.locationSelectedRegionLabel.setText("")
    
    def onLocationRegionItemChanged(self, item):
        if not item:
            return
        if self.layerManager.processingConfig.arsCode:
            if self.layerManager.processingConfig.arsCode.name == item.text():
                return

        self.locationSelectedRegionLabel.setText(item.text())
        code = ARS_INDEX.getARSCodeByName(item.text())
        if not code:
            return
        
        self.layerManager.processingConfig.setARSCode(code)
        self.layerManager.updateProjectName()

        self.locationProjectNameEdit.setText(self.layerManager.projectName)

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
        if self.centerLOCSuroundingCheck.isChecked():
            locs.append(LevelOfCentrality.Surounding)
        
        DialogState.CENTERPOINTS.value.setLOCs(locs)

    # SIGNALS
    def onCentralNextButton(self):
        self.centerUpdateContextLocsFromUi()
        self.stateMachine.transitionTo(DialogState.CENTERPOINTSEDIT)

    def onCentralGenerateButton(self):
        if self.guardLayerRegeneration(DialogState.CENTERPOINTS):
            return
        
        self.centerUpdateContextLocsFromUi()

        centerLayer = CenterLayer.loadFromFile(AUTO_CENTER_POINTS_PATH, self.layerManager.processingConfig.arsCode.code, DialogState.CENTERPOINTS.value.getLOCS())
        if centerLayer:
            DialogState.CENTERPOINTS.value.setCenterLayer(centerLayer)
            self.layerManager.update()
            self.showCenterPointsPage()
    
    def onCenterMapLayerComboBox(self):
        layer = self.centerMapLayerComboBox.currentLayer()
        if not layer:
            self.centerLoadLayerButton.setEnabled(False)
        else:
            self.centerLoadLayerButton.setEnabled(True)
        
    def onCenterLoadLayerButton(self):
        if self.guardLayerRegeneration(DialogState.CENTERPOINTS):
            return
        
        layer = self.centerMapLayerComboBox.currentLayer()
        if not layer:
            return
        
        if self.guardLayerCrsMistmatch(layer):
            return
                
        # Check if layer is a valid center layer
        try:
            # Set an empty ARSCodeStr and all LOCs because we do not want to filter anything
            centerLayer = CenterLayer.loadFromLayer(layer)
            if centerLayer:
                DialogState.CENTERPOINTS.value.setCenterLayer(centerLayer)
                self.layerManager.update()
                self.showCenterPointsPage()
        except Exception as e:
            QtHelper.showInformationBox(self, "Zentrenlayer", f"Keine valide Zentrenlayer: {e}")

    def onCenterAutoRadioButton(self):
        DialogState.CENTERPOINTS.value.setGenerateMethod(DirectRouteGenerateMethod.AUTO)
        self.showCenterPointsPage()

    def onCenterManualRadioButton(self):
        DialogState.CENTERPOINTS.value.setGenerateMethod(DirectRouteGenerateMethod.MANUEL)
        self.showCenterPointsPage()
    
    def onCenterLayerRadioButton(self):
        DialogState.CENTERPOINTS.value.setGenerateMethod(DirectRouteGenerateMethod.LAYER)
        self.showCenterPointsPage()
    
    ## CENTER EDIT PAGE

    # HELPERS
    def onCenterEditLeave(self):
        self.centerEditTool.restore()
        self.centerEditAddutton.setChecked(False)
        self.centerEditPropertiesButton.setChecked(False)
        self.centerEditGeometryButton.setChecked(False)
        self.centerEditDeleteButton.setChecked(False)

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
                self.layerManager.update()
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
            self.centerEditAddutton.setChecked(True)
            self.centerEditPropertiesButton.setChecked(False)
            self.centerEditGeometryButton.setChecked(False)
            self.centerEditDeleteButton.setChecked(False)

    def onCenterEditPropertiesButton(self):
        if self.centerEditTool:
            self.centerEditTool.setTool(CenterEditToolType.PropertyEdit)
            self.centerEditAddutton.setChecked(False)
            self.centerEditPropertiesButton.setChecked(True)
            self.centerEditGeometryButton.setChecked(False)
            self.centerEditDeleteButton.setChecked(False)

    def onCenterEditGeometryButton(self):
        if self.centerEditTool:
            self.centerEditTool.setTool(CenterEditToolType.MoveGeometry)
            self.centerEditAddutton.setChecked(False)
            self.centerEditPropertiesButton.setChecked(False)
            self.centerEditGeometryButton.setChecked(True)
            self.centerEditDeleteButton.setChecked(False)

    def onCenterEditDeleteButton(self):
        if self.centerEditTool:
            self.centerEditTool.setTool(CenterEditToolType.DeleteFeature)
            self.centerEditAddutton.setChecked(False)
            self.centerEditPropertiesButton.setChecked(False)
            self.centerEditGeometryButton.setChecked(False)
            self.centerEditDeleteButton.setChecked(True)

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
        directRouteLayer = DirectRouteNetworklayer(routeEntries, DirectRouteNetworklayer.LayerName)
        if directRouteLayer:
            DialogState.AIRLINE.value.setDirectRouteLayer(directRouteLayer)
            self.layerManager.update()
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
        
        if self.guardLayerCrsMistmatch(networkLayer):
            return
        
        DialogState.REPROJECT.value.setNetworklayer(networkLayer)

        if self.reprojectDetourToleranceCheckbox.isChecked():
            DialogState.REPROJECT.value.setDetourTolerance(self.reprojectDetourToleranceSpinbox.value() / 100.0)
        else:
            DialogState.REPROJECT.value.setDetourTolerance(0.0)
        
        DialogState.REPROJECT.value.setCenterDistanceTolerance(self.reprojectCenterDistanceToleranzSpinbox.value())

        task = RouteNetworkTask.createAndRunFromContextStateHandler(DialogState.context(), self.onReprojectGenerateResult, self.onReprojectGenerateProgressChanged)

        # task = RouteNetworkTask.createAndRunFromContextStateHandler(DialogState.context(), self.onReprojectGenerateResult, self.onReprojectGenerateProgressChanged)
        # Save the task into the context, so it does not get garbage collected
        DialogState.REPROJECT.value.setProcessing(task)
        DialogState.REPROJECT.value.setIsProcessing(True)

        task.start()
        self.showReprojectPage()
    
    def onReprojectGenerateResult(self, sucess: bool, taskResult: RouteNetworkTaskResult):
        if sucess:
            routeLayer = RouteNetworklayer(taskResult.routeEntries)
            DialogState.REPROJECT.value.setRouteLayer(routeLayer)
            # supplyNetworkLayer = SupplyNetworkElementLayer(taskResult.networkElements)
            # DialogState.REPROJECT.value.setSupplyNetworkLayer(supplyNetworkLayer)
            supplyAggregatedNetworkLayer = SupplyAggregatedNetworkElementLayer(taskResult.aggregatedElements)
            breakingPointsNetworkLayer = BreakingPointsNetworkLayer(taskResult.breakingPoints)
            missingRouteslayer = MissingRoutesLayer(taskResult.getMissingRoutes(), MissingRoutesLayer.LayerNameReproject, "Umlegung")
            DialogState.REPROJECT.value.setAggregatedSupplyNetworkLayer(supplyAggregatedNetworkLayer)
            DialogState.REPROJECT.value.setBreakingPointsNetworkLayer(breakingPointsNetworkLayer)
            if missingRouteslayer.routeEntries:
                DialogState.REPROJECT.value.setMissingRoutesLayer(missingRouteslayer)
                QtHelper.showInformationBox(
                    self,
                    "Fehlende Umlegungen",
                    f"Es konnten nicht alle Relationen umgelegt werden. Siehe dazu die Layer '{missingRouteslayer.groupName}.{missingRouteslayer.name()}'")
            self.layerManager.update()
        else:
            QgsMessageLog.logMessage(f"Error while processing: {taskResult.error}")
            
        DialogState.REPROJECT.value.setIsProcessing(False)
        
        self.showReprojectPage()
    
    def onReprojectGenerateProgressChanged(self, progress: RouteNetworkTaskProgress):
        oldValue = DialogState.REPROJECT.value.setProgress(progress)
        if progress.isDifferentTo(oldValue):
            self.showReprojectPage()
    
    def onReprojectCancelGenerateButton(self):
        task = DialogState.REPROJECT.value.getProcessing()
        if task:
            task.stop()
    
    def onReprojectDetourToleranceCheckbox(self):
        self.reprojectDetourToleranceSpinbox.setEnabled(self.reprojectDetourToleranceCheckbox.isChecked())

    
    # REPROJECT DEMAND PAGE
    def onReprojectDemandBackButton(self):
        self.stateMachine.transitionTo(DialogState.REPROJECT)

    def onReprojectDemandGenerateButton(self):
        if self.guardLayerRegeneration(DialogState.REPROJECTDEMAND):
            return
        
        directRouteLayer = DialogState.AIRLINE.value.getDirectRouteLayer()

        if not directRouteLayer:
            return
        networkLayer = self.reprojectDemandSelectLayer.currentLayer()
        if not networkLayer:
            return
        
        if self.guardLayerCrsMistmatch(networkLayer):
            return
        
        DialogState.REPROJECTDEMAND.value.setNetworklayer(networkLayer)

        demandFieldName = self.reprojectDemandSelectField.currentField()
        if not demandFieldName:
            return
        DialogState.REPROJECTDEMAND.value.setDemandFieldName(demandFieldName)
        
        if self.reprojectDetourToleranceCheckbox.isChecked():
            DialogState.REPROJECTDEMAND.value.setDetourTolerance(self.reprojectDemandDetourToleranceSpinbox.value() / 100.0)
        else:
            DialogState.REPROJECTDEMAND.value.setDetourTolerance(0.0)
        
        DialogState.REPROJECTDEMAND.value.setCenterDistanceTolerance(self.reprojectDemandCenterDistanceToleranzSpinbox.value())

        task = RouteNetworkTask.createAndRunFromContextStateHandler(DialogState.context(), self.onReprojectDemandGenerateResult, self.onReprojectDemandGenerateProgressChanged)
        # Save the task into the context, so it does not get garbage collected
        DialogState.REPROJECTDEMAND.value.setProcessing(task)
        DialogState.REPROJECTDEMAND.value.setIsProcessing(True)

        task.start()
        self.showReprojectPage()
    
    def onReprojectDemandSelectLayerChanged(self):
        networkLayer = self.reprojectDemandSelectLayer.currentLayer()
        if not networkLayer:
            return
        
        self.reprojectDemandSelectField.setLayer(networkLayer)
    
    def onReprojectDemandGenerateResult(self, sucess: bool, taskResult: RouteNetworkTaskResult):
        if sucess:
            routeLayer = RouteNetworklayer(taskResult.routeEntries, layerName="Umgelegte Nachfagerelationen", groupName="Nachfrageumlegung")
            DialogState.REPROJECTDEMAND.value.setRouteLayer(routeLayer)
            supplyAggregatedNetworkLayer = SupplyAggregatedNetworkElementLayer(taskResult.aggregatedElements, layerName="Nachfragenetz (aggregiert)", groupName="Nachfrageumlegung")
            breakingPointsNetworkLayer = BreakingPointsNetworkLayer(taskResult.breakingPoints, layerName="Netzaufteilung (Nachfrage)", groupName="Nachfrageumlegung")
            missingRouteslayer = MissingRoutesLayer(taskResult.getMissingRoutes(), MissingRoutesLayer.LayerNameReprojectDemand, "Nachfrageumlegung")
            DialogState.REPROJECTDEMAND.value.setAggregatedSupplyNetworkLayer(supplyAggregatedNetworkLayer)
            DialogState.REPROJECTDEMAND.value.setBreakingPointsNetworkLayer(breakingPointsNetworkLayer)
            if missingRouteslayer.routeEntries:
                DialogState.REPROJECTDEMAND.value.setMissingRoutesLayer(missingRouteslayer)
                QtHelper.showInformationBox(
                    self,
                    "Fehlende Umlegungen",
                    f"Es konnten nicht alle Relationen umgelegt werden. Siehe dazu die Layer '{missingRouteslayer.groupName}.{missingRouteslayer.name()}'")

            self.layerManager.update()
        else:
            QgsMessageLog.logMessage(f"Error while processing: {taskResult.error}")
        
        DialogState.REPROJECTDEMAND.value.setIsProcessing(False)

        self.showReprojectDemandPage()
    
    def onReprojectDemandGenerateProgressChanged(self, progress: RouteNetworkTaskProgress):
        oldValue = DialogState.REPROJECTDEMAND.value.setProgress(progress)
        if progress.isDifferentTo(oldValue):
            self.showReprojectDemandPage()
    
    def onReprojectDemandCancelGenerateButton(self):
        task = DialogState.REPROJECTDEMAND.value.getProcessing()
        if task:
            task.stop()
    
    def onReprojectDemandDetourToleranceCheckbox(self):
        self.reprojectDemandDetourToleranceSpinbox.setEnabled(self.reprojectDemandDetourToleranceCheckbox.isChecked())
    
    def onReprojectDemandCenterDistanceLabel(self):
        QtHelper.showInformationBox(self, "Zentrenverknüpfungsdistanz", "Maximal valide Distanz zwischen einem Zentrenpunkt und einer Netzkante.")