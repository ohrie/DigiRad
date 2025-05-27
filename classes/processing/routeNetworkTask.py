from typing import Self, Tuple

from qgis.core import (
    QgsTask,
    QgsMessageLog,
    Qgis,
    QgsVectorLayer,
    QgsApplication,
)
from qgis.PyQt.QtCore import pyqtSignal

from ..layers.directRouteNetworkLayer import DirectRouteNetworklayer
from .routeNetwork import NetworkPathFinder, RouteEntry

class RouteNetworkTask(QgsTask):
    # Signals for communication
    progressChanged = pyqtSignal(int)
    resultReady = pyqtSignal(object)
    
    def __init__(self, networkLayer: QgsVectorLayer, directRouteLayer: DirectRouteNetworklayer):
        super().__init__("Luftlinienrouten auf Verkehrsnetz projizieren", QgsTask.CanCancel)
        self.networkLayer = networkLayer
        self.directRouteLayer = directRouteLayer
        self.result = None
        self.exception = None
    
    @staticmethod
    def createAndRunTask(networkLayer: QgsVectorLayer, directRouteLayer: DirectRouteNetworklayer, resultCallback = None, progressCallback = None) -> Self:
        task = RouteNetworkTask(networkLayer, directRouteLayer)
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
            self.setProgress(10)
            self.progressChanged.emit(10)
            pathFinder = NetworkPathFinder(self.networkLayer)
            entries = list(self.directRouteLayer.routeEntries)[0:]

            # Step 1: Build the graph
            QgsMessageLog.logMessage("Building graph..")
            pathFinder.buildGraph(entries)
            self.setProgress(50)
            self.progressChanged.emit(50)
            QgsMessageLog.logMessage("Done.")
            # Check if task was cancelled
            if self.isCanceled():
                return False
            
            # Step 2: Route between the relation start and end points
            relationsLen = len(entries)
            resultEntries = []
            QgsMessageLog.logMessage("Finding paths..")
            for i, routeEntry in enumerate(entries):
                # Check if task was cancelled
                if self.isCanceled():
                    return False
                (pathPoints, cost) = pathFinder.findPathOfRelation(routeEntry.relationId)
                if not pathPoints:
                    QgsMessageLog.logMessage(f"No path found for relation {routeEntry.relationId}")
                
                # Update progress (0-100)
                progress = 50 + int((i + 1) / relationsLen * 50)
                self.setProgress(progress)
                self.progressChanged.emit(progress)
                
                resultEntries.append(RouteEntry(routeEntry, pathPoints, cost))
            
            QgsMessageLog.logMessage("Done.")
            self.result = resultEntries
            self.setProgress(100)
            self.progressChanged.emit(100)

            return True
            
        except Exception as e:
            self.exception = e
            return False
    
    def finished(self, result):
        """Called when task completes (runs in main thread)"""

        QgsMessageLog.logMessage('HERE!')
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