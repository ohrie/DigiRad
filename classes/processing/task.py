from typing import Dict, List

from qgis.core import (
    QgsMessageLog,
    QgsVectorLayer,
    QgsWkbTypes,
    QgsFeature,
    QgsGeometry,
)
from qgis.PyQt.QtCore import pyqtSignal, QTimer, QThread

from .routeNetwork import NetworkPathFinder, RouteEntry, RouteGenerationOptions, InnerDirectRouteEntry
from ..network import ConnectivityFunction
from ...dialogstate import DialogState, DialogStateContext, ReprojectHandler, AirlineHandler, ReprojectDemandHandler
from .routing.demandRouting import DemandNetworkStrategy, NetworkDemandProperties
from .routeNetworkTaskHelpers import RouteNetworkTaskResult, RouteNetworkTaskProgress
from .routeNetworkAnalyser import RouteNetworkAnalyser

class RouteNetworkWorker(QThread):
    """Worker that will live in a separate thread"""
    progressChanged = pyqtSignal(object) # progress (0 - 100), status text, RouteNetworkTaskProgress
    finished = pyqtSignal(bool, object)  # success, result
    
    def __init__(self, networkLayerData: dict, directRouteLayerEntries: List[InnerDirectRouteEntry], options: RouteGenerationOptions):
        super().__init__()
        self.networkLayerData = networkLayerData
        self.directRouteLayerEntries = directRouteLayerEntries
        self.options = options
        self.shouldStop = False
        self.progress = 0
        self.graphGenTimer = QTimer()
        self.graphGenTimer.timeout.connect(self._onGraphGenTimerTimeout)
        
    def run(self):
        """Main work method - runs in the worker thread"""
        try:
            self.setProgress(0, "Verkehrsnetz übertragen..")
            # Create QObjects here - they belong to the worker thread
            memoryLayer = RouteNetworkWorker._createLayerFromData(self.networkLayerData)

            self.result = None
            entries = self.directRouteLayerEntries

            sortedEntries = {}
            for entry in entries:
                if entry.cf in sortedEntries:
                    sortedEntries[entry.cf].append(entry)
                else:
                    sortedEntries[entry.cf] = [entry]

            # Step 1: Build the graph
            self.setProgress(5, "Graphen erzeugen..")
            # Start a dummy timer which bumps up the progress to indicate the graph
            # generation progress to the user
            self.graphGenTimer.start(self._determineGraphGenTimerTiming(len(self.networkLayerData["features"])))
            # if not self.pathFinder:
            self.pathFinder = NetworkPathFinder(memoryLayer, self.options)
            QgsMessageLog.logMessage("Building graph..")
            self.pathFinder.buildGraph(entries)
            # else:
            #     self.pathFinder.cleanUp()
            self.graphGenTimer.stop()
            self.setProgress(40, "Beginne Umlegung..")
            # Check if task was cancelled
            if self.shouldStop:
                return False
            
            # Step 2: 1st Route between the relation start and end points
            QgsMessageLog.logMessage("First routing..")
            if self.options.isDetourActive():
                relationsLen = len(entries) * 2
            else:
                relationsLen = len(entries)

            resultEntries = self._findRouteEntries(sortedEntries, self.options.isDetourActive(), 0, relationsLen, 55)
            self.pathFinder.graphModifier.modifyEdgeCostsBasedOnChangelog()

            # Step 3: 2nd/last Route between the relation start and end points
            if self.options.isDetourActive():
                QgsMessageLog.logMessage("Optimized routing..")
                resultEntries = self._findRouteEntries(sortedEntries, False, len(entries), relationsLen, 55)
            
            # Step 4: Do network analysis
            self.setProgress(95, "Analysiere Umlegung..")
            networkAnalyser = RouteNetworkAnalyser(self.pathFinder.graph, resultEntries)
            networkElements = networkAnalyser.createNetworkElements()
            (aggregatedElements, breakingPoints) = networkAnalyser.aggregateElements(networkElements)

            # QgsMessageLog.logMessage("Cleaning up..")
            # self.pathFinder.cleanUp()
            QgsMessageLog.logMessage("Done.")
            result = RouteNetworkTaskResult.createSuccess(resultEntries, networkElements, aggregatedElements, breakingPoints)
            
            self.finished.emit(True, result)
            
        except Exception as e:
            QgsMessageLog.logMessage(str(e))
            self.finished.emit(False, RouteNetworkTaskResult.createError(str(e)))
        finally:
            self.setProgress(100, "Abgeschlossen.")
            self.shouldStop = True
    
    def _findRouteEntries(
            self,
            sortedEntries: Dict[ConnectivityFunction, List[InnerDirectRouteEntry]],
            modifyGraph: bool,
            progressProcessedStart: int,
            progressProcessMax: int,
            progressProcessMultiplier: float) -> List[RouteEntry]:
        routeEntries = []
        for cf in ConnectivityFunction:
            if not cf in sortedEntries:
                continue
            subEntries = sortedEntries[cf][0:]

            QgsMessageLog.logMessage(f"Finding paths for {cf.asStr()} ({len(subEntries)} relations)..")
            for (i, routeEntry) in enumerate(subEntries):
                progressProcessedStart += 1
                # Check if task was cancelled
                if self.shouldStop:
                    return False
                
                routeResult = self.pathFinder.findPathOfRelation(routeEntry.relationId, modifyGraph)
                
                if not routeResult:
                    QgsMessageLog.logMessage(f"No path found for relation {routeEntry.relationId}")
                
                progress = 40 + int((progressProcessedStart + 1) / progressProcessMax * progressProcessMultiplier)

                self.setProgress(progress, "[{}] Relation {} von {} (Durchgang {})".format(
                                              cf.asStrShort(),
                                              i + 1,
                                              len(subEntries),
                                              "1" if modifyGraph else "2"))
                
                routeEntries.append(RouteEntry(routeEntry, routeResult))

        return routeEntries
    
    def stop(self):
        """Signal worker to stop"""
        self.shouldStop = True
        self.finished.emit(False, RouteNetworkTaskResult.createError("Stopped"))
    
    def setProgress(self, progress: int, message: str = ""):
        progress = min(progress, 100)
        self.progress = progress
        self.progressChanged.emit(RouteNetworkTaskProgress(progress, message))
    
    def _determineGraphGenTimerTiming(self, featureCount: int) -> int:
        if featureCount < 10000:
            return 100
        elif featureCount < 30000:
            return 200
        else:
            return 1000

    def _onGraphGenTimerTimeout(self):
        QgsMessageLog.logMessage("timer.")
        if self.shouldStop:
            self.graphGenTimer.stop()
            return
        QgsMessageLog.logMessage("timer 2")
        
        self.setProgress(self.progress + 1)
    
    @staticmethod
    def _createLayerFromData(layerData: dict) -> QgsVectorLayer:
        """Recreate a memory layer in the background task from a dict (created by RouteNetworkTask._createMemorylayerFromVector)"""
        memoryLayer = QgsVectorLayer(layerData['uri'], layerData['name'], "memory")
        
        provider = memoryLayer.dataProvider()
        features = []
        for featData in layerData['features']:
            feature = QgsFeature()
            if featData['geometry']:
                feature.setGeometry(QgsGeometry.fromWkt(featData['geometry']))
            feature.setAttributes(featData['attributes'])
            features.append(feature)
        
        provider.addFeatures(features)
        memoryLayer.updateExtents()
        return memoryLayer
    
class RouteNetworkTask:
    """Manager class that handles the thread setup"""
    
    def __init__(self, networkLayerData: dict, directRouteLayerEntries: List[InnerDirectRouteEntry], options: RouteGenerationOptions, resultCallback, progressCallback):
        self.thread = RouteNetworkWorker(networkLayerData, directRouteLayerEntries, options)  # Create the thread

        # Connect signals
        if progressCallback:
            self.thread.progressChanged.connect(progressCallback)
        if resultCallback:
            self.thread.finished.connect(resultCallback)
        
        # Cleanup when done
        self.thread.finished.connect(self.thread.deleteLater)
        
    @staticmethod
    def createAndRunFromContextStateHandler(context: DialogStateContext, resultCallback = None, progressCallback = None) -> 'RouteNetworkTask':
        directRouteLayer = context.get(AirlineHandler.KDirectRouteLayer)

        if context.currentState == DialogState.REPROJECT:
            networkLayer = context.get(ReprojectHandler.KNetworkLayer)
            detourTolerance = context.get(ReprojectHandler.KDetourTolerance)
            options = RouteGenerationOptions(detourTolerance)
        elif context.currentState == DialogState.REPROJECTDEMAND:
            networkLayer = context.get(ReprojectDemandHandler.KNetworkLayer)
            demandFieldName = context.get(ReprojectDemandHandler.KDemandFieldName)
            detourTolerance = context.get(ReprojectDemandHandler.KDetourTolerance)
            networkStrategy = DemandNetworkStrategy(NetworkDemandProperties.fromLayer(networkLayer, demandFieldName))
            options = RouteGenerationOptions(detourTolerance, networkStrategy=networkStrategy)
        
        networkLayerData = RouteNetworkTask._createMemorylayerFromVector(networkLayer)
        directRouteLayerEntries = []
        for entry in directRouteLayer.routeEntries:
            directRouteLayerEntries.append(InnerDirectRouteEntry(entry))

        task = RouteNetworkTask(networkLayerData, directRouteLayerEntries, options, resultCallback=resultCallback, progressCallback=progressCallback)
        
        return task
    
    def start(self):
        """Start the background processing"""
        self.thread.start()
    
    def stop(self):
        """Stop the background processing"""
        if self.thread.isRunning():
            self.thread.stop()
            self.thread.quit()
            self.thread.wait(5000)  # Wait up to 5 seconds
    
    def _on_finished(self, success, result):
        """Handle worker completion"""
        if self.result_callback:
            self.result_callback(success, result)
    
    @staticmethod
    def _createMemorylayerFromVector(originalLayer: QgsVectorLayer) -> dict:
        """Create memory layer data that can be safely used in background thread"""
        
        # Get layer info
        geom_type = QgsWkbTypes.displayString(originalLayer.wkbType())
        crs_authid = originalLayer.crs().authid()
        
        # Build memory layer URI
        uri = f"LineString?crs={crs_authid}"
        
        # Add field definitions to URI
        fields = originalLayer.fields()
        fieldDefs = []
        for field in fields:
            fieldDefs.append(f"field={field.name()}:{field.typeName()}")
        
        if fieldDefs:
            uri += "&" + "&".join(fieldDefs)
        
        # Copy features data
        featuresData = []
        for feature in originalLayer.getFeatures():
            featureDict = {
                "geometry": feature.geometry().asWkt() if feature.hasGeometry() else None,
                "attributes": feature.attributes()
            }
            featuresData.append(featureDict)
        
        return {
            "uri": uri,
            "features": featuresData,
            "name": originalLayer.name()
        }