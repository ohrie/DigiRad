from typing import Self, Tuple, Dict, List

from qgis.core import (
    QgsTask,
    QgsMessageLog,
    Qgis,
    QgsVectorLayer,
    QgsApplication,
)
from qgis.PyQt.QtCore import pyqtSignal

from ..layers.directRouteNetworkLayer import DirectRouteNetworklayer
from .directRouteNetwork import DirectRouteEntry
from .routeNetwork import NetworkPathFinder, RouteEntry, RouteGenerationOptions
from ..network import ConnectivityFunction
from ...dialogstate import DialogStateContext, ReprojectHandler, AirlineHandler

class RouteNetworkTask(QgsTask):
    # Signals for communication
    progressChanged = pyqtSignal(int)
    resultReady = pyqtSignal(object)
    
    def __init__(self, networkLayer: QgsVectorLayer, directRouteLayer: DirectRouteNetworklayer, options: RouteGenerationOptions, pathFinder: NetworkPathFinder = None):
        super().__init__("Luftlinienrouten auf Verkehrsnetz projizieren", QgsTask.CanCancel)
        self.networkLayer = networkLayer
        self.directRouteLayer = directRouteLayer
        self.pathFinder = pathFinder
        self.options = options
        self.result = None
        self.exception = None
    
    @staticmethod
    def createAndRunFromContextStateHandler(context: DialogStateContext, resultCallback = None, progressCallback = None) -> Self:
        directRouteLayer = context.get(AirlineHandler.KDirectRouteLayer)
        networkLayer = context.get(ReprojectHandler.KNetworkLayer)
        pathFinder = context.get(ReprojectHandler.KPathfinder)
        detourTolerance = context.get(ReprojectHandler.KDetourTolerance)

        options = RouteGenerationOptions(detourTolerance)

        task = RouteNetworkTask(networkLayer, directRouteLayer, options, pathFinder)
        
        if resultCallback:
            task.resultReady.connect(resultCallback)
        if progressCallback:
            task.progressChanged.connect(progressCallback)
        
        task_manager = QgsApplication.taskManager()
        task_manager.addTask(task)
        
        return task
    
    @staticmethod
    def createAndRunTask(networkLayer: QgsVectorLayer, directRouteLayer: DirectRouteNetworklayer, options: RouteGenerationOptions, resultCallback = None, progressCallback = None) -> Self:
        task = RouteNetworkTask(networkLayer, directRouteLayer, options, pathFinder=None)
        if resultCallback:
            task.resultReady.connect(resultCallback)
        if progressCallback:
            task.progressChanged.connect(progressCallback)
        
        task_manager = QgsApplication.taskManager()
        task_manager.addTask(task)
        
        return task
        
    def run(self):
        """This method runs in the background thread"""
        try:
            self.result = None
            entries = list(self.directRouteLayer.routeEntries)[0:]

            sortedEntries = {}
            for entry in entries:
                if entry.cf in sortedEntries:
                    sortedEntries[entry.cf].append(entry)
                else:
                    sortedEntries[entry.cf] = [entry]

            # Step 1: Build the graph
            self.setProgress(5)
            self.progressChanged.emit(5)
            # if not self.pathFinder:
            self.pathFinder = NetworkPathFinder(self.networkLayer, self.options)
            QgsMessageLog.logMessage("Building graph..")
            self.pathFinder.buildGraph(entries)
            # else:
            #     self.pathFinder.cleanUp()
            self.setProgress(40)
            self.progressChanged.emit(40)
            # Check if task was cancelled
            if self.isCanceled():
                return False
            
            # Step 2: 1st Route between the relation start and end points
            QgsMessageLog.logMessage("First routing..")
            if self.options.isDetourActive():
                relationsLen = len(entries) * 2
            else:
                relationsLen = len(entries)

            resultEntries = self._findRouteEntries(sortedEntries, self.options.isDetourActive(), 0, relationsLen, 60)
            self.pathFinder.graphModifier.modifyEdgeCostsBasedOnChangelog()

            # Step 3: 2nd/last Route between the relation start and end points
            if self.options.isDetourActive():
                QgsMessageLog.logMessage("Optimized routing..")
                resultEntries = self._findRouteEntries(sortedEntries, False, len(entries), relationsLen, 60)
            
            # QgsMessageLog.logMessage("Cleaning up..")
            # self.pathFinder.cleanUp()
            QgsMessageLog.logMessage("Done.")
            self.result = RouteNetworkTaskResult(resultEntries, self.pathFinder)
            self.setProgress(100)
            self.progressChanged.emit(100)

            return True
            
        except Exception as e:
            self.exception = e
            return False
    
    def _findRouteEntries(
            self,
            sortedEntries: Dict[ConnectivityFunction, List[DirectRouteEntry]],
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
            for routeEntry in subEntries:
                progressProcessedStart += 1
                # Check if task was cancelled
                if self.isCanceled():
                    return False
                routeResult = self.pathFinder.findPathOfRelation(routeEntry.relationId, modifyGraph)
                
                if not routeResult:
                    QgsMessageLog.logMessage(f"No path found for relation {routeEntry.relationId}")
                
                # Update progress (0-100)
                progress = 40 + int((progressProcessedStart + 1) / progressProcessMax * progressProcessMultiplier)
                self.setProgress(progress)
                self.progressChanged.emit(progress)
                
                routeEntries.append(RouteEntry(routeEntry, routeResult))

        return routeEntries
    
    def finished(self, result):
        """Called when task completes (runs in main thread)"""

        # `result` is the return value from `self.run`.
        if result:
            QgsMessageLog.logMessage('Task completed successfully!', 
                                   'DigiRad', Qgis.Success)
            # Emit signal with results
            self.resultReady.emit((True, self.result))
        else:
            if self.exception:
                QgsMessageLog.logMessage(f'Task failed: {self.exception}', 
                                       'DigiRad', Qgis.Critical)
                self.resultReady.emit((False, self.exception))
            else:
                QgsMessageLog.logMessage('Task was cancelled', 
                                       'DigiRad', Qgis.Warning)
                self.resultReady.emit((False, None))
    
    def cancel(self):
        """Called when task is cancelled"""
        QgsMessageLog.logMessage('Task cancelled by user', 
                               'DigiRad', Qgis.Info)
        super().cancel()

class RouteNetworkTaskResult:
    def __init__(self, routeEntries: List[RouteEntry], pathFinder: NetworkPathFinder):
      self.routeEntries = routeEntries
      self.pathFinder = pathFinder