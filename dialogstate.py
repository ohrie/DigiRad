from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from abc import ABC, abstractmethod

from qgis.core import QgsVectorLayer, QgsMessageLog

from .classes.network import LevelOfCentrality
from .classes.layers.centerLayer import CenterLayer
from .classes.layers.routeNetworkLayer import RouteNetworklayer
from .classes.layers.directRouteNetworkLayer import DirectRouteNetworklayer, MissingRoutesLayer
from .classes.layers.analysisLayers import SupplyNetworkElementLayer, SupplyAggregatedNetworkElementLayer, BreakingPointsNetworkLayer
from .classes.processing.directRouteNetwork import DirectRouteGenerateMethod
from .classes.processing.routeNetwork import NetworkPathFinder
from .classes.processing.routeNetworkTaskHelpers import RouteNetworkTaskProgress

class StateHandler(ABC):
    """Base class for state handlers"""
    
    def __init__(self, name: str):
        self.name = name
        self.context_data = {}
        self.context = None
    
    def setUi(self, ui):
        """Set the UI reference"""
        self.ui = ui
    
    def setContext(self, context: 'DialogStateContext'):
        """Set the context reference"""
        self.context = context
    
    def getContext(self) -> 'DialogStateContext':
        return self.context
    
    @abstractmethod
    def onEnter(self, previousState: Optional['DialogState'] = None):
        """Called when entering this state"""
        pass
    
    @abstractmethod
    def onExit(self, nextState: Optional['DialogState'] = None):
        """Called when exiting this state"""
        pass
    
    @abstractmethod
    def handleUi(self):
        """Handle UI for this state"""
        pass
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        """Check if transition to target state is allowed"""
        return True

class WelcomeHandler(StateHandler):
    def __init__(self):
        super().__init__("Welcome")
    
    def onEnter(self, previousState: Optional['DialogState'] = None):
        # Clear the context state because we most likely want to restart
        # the project
        self.context.clear()
        self.handleUi()
    
    def onExit(self, nextState: Optional['DialogState'] = None):
        pass
    
    def handleUi(self):
        if self.ui:
            self.ui.showWelcomePage()
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        return targetState == DialogState.LCOATIONSELECT

class LocationSelectHandler(StateHandler):
    KBaseLayer = "location.BaseLayer"

    def __init__(self):
        super().__init__("LocationSelect")
    
    def onEnter(self, previousState: Optional['DialogState'] = None):
        # Clear the context state, if we do not come from the welcome state,
        # because we most likely want to restart the project
        if previousState != DialogState.WELCOME:
            self.context.clear()
        self.handleUi()
    
    def onExit(self, nextState: Optional['DialogState'] = None):
        pass
    
    def handleUi(self):
        if self.ui:
            self.ui.showLocationSelectPage()
    
    def canTransitionTo(self, targetState):
        return targetState in [DialogState.WELCOME, DialogState.CENTERPOINTS]
    
    def hasBaseLayerStr(self) -> bool:
        return self.context.has(LocationSelectHandler.KBaseLayer)
    
    def getBaseLayerStr(self) -> Optional[str]:
        return self.context.get(LocationSelectHandler.KBaseLayer)
    
    def setBaseLayerStr(self, value: str) -> Optional[str]:
        return self.context.updateValue(LocationSelectHandler.KBaseLayer, value)

class CenterPointsHandler(StateHandler):
    KCenterLayer = "center.CenterLayer"
    KGenerateMethod = "center.GenerateMethod"
    KLOCs = "center.LOCs"
    LayerKeys = [KCenterLayer]

    def __init__(self):
        super().__init__("CenterPoints")
    
    def onEnter(self, previousState: Optional['DialogState'] = None):
        self.handleUi()
    
    def onExit(self, nextState: Optional['DialogState'] = None):
        pass
    
    def handleUi(self):
        if self.ui:
            self.ui.showCenterPointsPage()
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        return targetState in [DialogState.WELCOME, DialogState.LCOATIONSELECT, DialogState.CENTERPOINTSEDIT]
    
    def hasCenterLayer(self) -> bool:
        return self.context.has(CenterPointsHandler.KCenterLayer)
    
    def getCenterLayer(self) -> Optional[CenterLayer]:
        return self.context.get(CenterPointsHandler.KCenterLayer)
    
    def setCenterLayer(self, value: CenterLayer) -> Optional[CenterLayer]:
        DialogState.deleteValuesAfterContext(DialogState.CENTERPOINTS, "LayerKeys")
        return self.context.updateValue(CenterPointsHandler.KCenterLayer, value)
    
    def getGenerateMethod(self) -> DirectRouteGenerateMethod:
        return self.context.getOrSetDefault(CenterPointsHandler.KGenerateMethod, default=DirectRouteGenerateMethod.default())
    
    def setGenerateMethod(self, value: DirectRouteGenerateMethod) -> Optional[DirectRouteGenerateMethod]:
        return self.context.updateValue(CenterPointsHandler.KGenerateMethod, value, default=DirectRouteGenerateMethod.default())
    
    def getLOCS(self) -> List[LevelOfCentrality]:
        return self.context.getOrSetDefault(CenterPointsHandler.KLOCs, default=LevelOfCentrality.defaults())
    
    def setLOCs(self, value: List[LevelOfCentrality]) -> Optional[List[LevelOfCentrality]]:
        return self.context.updateValue(CenterPointsHandler.KLOCs, value, default=LevelOfCentrality.defaults())

class CenterPointsEditHandler(StateHandler):
    def __init__(self):
        super().__init__("CenterPointsEdit")
    
    def onEnter(self, previousState: Optional['DialogState'] = None):
        self.handleUi()

    def onExit(self, nextState: Optional['DialogState'] = None):
        centerLayer = DialogState.CENTERPOINTS.value.getCenterLayer()
        if not centerLayer:
            return
        
        centerLayer.qgsLayer().commitChanges()
        centerLayer.update()
    
    def handleUi(self):
        if self.ui:
            self.ui.showCenterPointsEditPage()
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        return targetState in [DialogState.WELCOME, DialogState.LCOATIONSELECT, DialogState.CENTERPOINTS, DialogState.AIRLINE]

class AirlineHandler(StateHandler):
    KDirectRouteLayer = "airline.DirectRouteLayer"
    LayerKeys = [KDirectRouteLayer]

    def __init__(self):
        super().__init__("Airline")
    
    def onEnter(self, previousState: Optional['DialogState'] = None):
        self.handleUi()
    
    def onExit(self, nextState: Optional['DialogState'] = None):
        pass
    
    def handleUi(self):
        if self.ui:
            self.ui.showAirlinePage()
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        return targetState in [DialogState.WELCOME, DialogState.LCOATIONSELECT, DialogState.CENTERPOINTSEDIT, DialogState.REPROJECT, DialogState.REPROJECTDEMAND]
    
    def getDirectRouteLayer(self) -> Optional[DirectRouteNetworklayer]:
        return self.context.get(AirlineHandler.KDirectRouteLayer)
    
    def setDirectRouteLayer(self, value: DirectRouteNetworklayer) -> DirectRouteNetworklayer:
        DialogState.deleteValuesAfterContext(DialogState.AIRLINE, "LayerKeys")
        return self.context.updateValue(AirlineHandler.KDirectRouteLayer, value)
    
    def hasDirectRouteLayer(self) -> bool:
        return self.context.has(AirlineHandler.KDirectRouteLayer)

class ReprojectHandler(StateHandler):
    KProcessing = "reproject.Processing"
    KIsProcessing = "reproject.Isprocessing"
    KProgress = "reproject.Progress"
    KDetourTolerance = "reproject.DetourTolerance"
    KPathfinder = "reproject.Pathfinder"
    KNetworkLayer = "reproject.Networklayer"
    KRouteLayer = "reproject.RouteLayer"
    KSupplyNetworkLayer = "reproject.SupplyNetworkLayer"
    KAggregatedSupplyNetworkLayer = "reproject.KAggregatedSupplyNetworkLayer"
    KBreakingPointsNetworkLayer = "reproject.KBreakingPointsNetworkLayer"
    KMissingRoutesLayer = "reproject.KMissingRoutesLayer"
    KCenterDistanceTolerance = "reproject.KCenterDistanceTolerance"

    LayerKeys = [
        KNetworkLayer,
        KRouteLayer,
        KSupplyNetworkLayer,
        KAggregatedSupplyNetworkLayer,
        KBreakingPointsNetworkLayer,
        KMissingRoutesLayer
        ]

    def __init__(self):
        super().__init__("Reproject")
    
    def onEnter(self, previousState: Optional['DialogState'] = None):
        self.handleUi()
    
    def onExit(self, nextState: Optional['DialogState'] = None):
        pass
    
    def handleUi(self):
        if self.ui:
            self.ui.showReprojectPage()
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        return targetState in [DialogState.WELCOME, DialogState.LCOATIONSELECT, DialogState.AIRLINE, DialogState.REPROJECTDEMAND]
    
    def setIsProcessing(self, value: bool) -> bool:
        self.context.set(ReprojectHandler.KIsProcessing, value)

    def isProcessing(self) -> bool:
        return self.context.get(ReprojectHandler.KIsProcessing, False)
    
    def getProcessing(self) -> Optional[Any]:
        return self.context.get(ReprojectHandler.KProcessing)
    
    def setProcessing(self, value: Optional[Any]):
        self.context.set(ReprojectHandler.KProcessing, value)
    
    def getProgress(self) -> RouteNetworkTaskProgress:
        return self.context.get(ReprojectHandler.KProgress, RouteNetworkTaskProgress(0))
    
    def setProgress(self, value: RouteNetworkTaskProgress) -> RouteNetworkTaskProgress:
        return self.context.updateValue(ReprojectHandler.KProgress, value, default=RouteNetworkTaskProgress(0))
    
    def getDetourTolerance(self) -> float:
        return self.context.get(ReprojectHandler.KDetourTolerance, 1)
    
    def setDetourTolerance(self, value: float) -> float:
        return self.context.updateValue(ReprojectHandler.KDetourTolerance, value)
    
    def getNetworklayer(self) -> Optional[QgsVectorLayer]:
        return self.context.get(ReprojectHandler.KNetworkLayer)
    
    def setNetworklayer(self, value: QgsVectorLayer) -> QgsVectorLayer:
        DialogState.deleteValuesAfterContext(DialogState.REPROJECT, "LayerKeys")
        return self.context.updateValue(ReprojectHandler.KNetworkLayer, value)
    
    def getPathfinder(self) -> Optional[NetworkPathFinder]:
        return self.context.get(ReprojectHandler.KPathfinder)
    
    def setPathfinder(self, value: NetworkPathFinder) -> Optional[NetworkPathFinder]:
        return self.context.updateValue(ReprojectHandler.KPathfinder, value)
    
    def getRouteLayer(self) -> Optional[RouteNetworklayer]:
        return self.context.get(ReprojectHandler.KRouteLayer)
    
    def setRouteLayer(self, value: RouteNetworklayer) -> Optional[RouteNetworklayer]:
        DialogState.deleteValuesAfterContext(DialogState.REPROJECT, "LayerKeys")
        return self.context.updateValue(ReprojectHandler.KRouteLayer, value)
    
    def hasRouteLayer(self) -> bool:
        return self.context.has(ReprojectHandler.KRouteLayer)
    
    def getSupplyNetworkLayer(self) -> Optional[SupplyNetworkElementLayer]:
        return self.context.get(ReprojectHandler.KSupplyNetworkLayer)
    
    def setSupplyNetworkLayer(self, value: SupplyNetworkElementLayer) -> Optional[SupplyNetworkElementLayer]:
        DialogState.deleteValuesAfterContext(DialogState.REPROJECT, "LayerKeys")
        return self.context.updateValue(ReprojectHandler.KSupplyNetworkLayer, value)
    
    def hasSupplyNetworkLayer(self) -> bool:
        return self.context.has(ReprojectHandler.KSupplyNetworkLayer)
    
    def setAggregatedSupplyNetworkLayer(self, value: SupplyAggregatedNetworkElementLayer) -> Optional[SupplyAggregatedNetworkElementLayer]:
        DialogState.deleteValuesAfterContext(DialogState.REPROJECT, "LayerKeys")
        return self.context.updateValue(ReprojectHandler.KAggregatedSupplyNetworkLayer, value)
    
    def setBreakingPointsNetworkLayer(self, value: BreakingPointsNetworkLayer) -> Optional[BreakingPointsNetworkLayer]:
        DialogState.deleteValuesAfterContext(DialogState.REPROJECT, "LayerKeys")
        return self.context.updateValue(ReprojectHandler.KBreakingPointsNetworkLayer, value)
    
    def setMissingRoutesLayer(self, value: MissingRoutesLayer) -> Optional[MissingRoutesLayer]:
        DialogState.deleteValuesAfterContext(DialogState.REPROJECT, "LayerKeys")
        return self.context.updateValue(ReprojectHandler.KMissingRoutesLayer, value)
    
    def setCenterDistanceTolerance(self, value: int) -> Optional[int]:
        return self.context.updateValue(ReprojectHandler.KCenterDistanceTolerance, value)

class ReprojectDemandHandler(StateHandler):
    KProcessing = "reprojectDemand.Processing"
    KIsProcessing = "reprojectDemand.Isprocessing"
    KProgress = "reprojectDemand.Progress"
    KDetourTolerance = "reprojectDemand.DetourTolerance"
    KDemandFieldName = "reprojectDemand.DemandFieldName"
    KPathfinder = "reprojectDemand.Pathfinder"
    KNetworkLayer = "reprojectDemand.Networklayer"
    KRouteLayer = "reprojectDemand.RouteLayer"
    KSupplyNetworkLayer = "reprojectDemand.SupplyNetworkLayer"
    KAggregatedSupplyNetworkLayer = "reprojectDemand.KAggregatedSupplyNetworkLayer"
    KBreakingPointsNetworkLayer = "reprojectDemand.KBreakingPointsNetworkLayer"
    KMissingRoutesLayer = "reproject.KMissingRoutesLayer"
    KCenterDistanceTolerance = "reproject.KCenterDistanceTolerance"

    LayerKeys = [
        KNetworkLayer,
        KRouteLayer,
        KSupplyNetworkLayer,
        KAggregatedSupplyNetworkLayer,
        KBreakingPointsNetworkLayer,
        KMissingRoutesLayer
        ]

    def __init__(self):
        super().__init__("ReprojectDemand")
    
    def onEnter(self, previousState: Optional['DialogState'] = None):
        self.handleUi()
    
    def onExit(self, nextState: Optional['DialogState'] = None):
        pass
    
    def handleUi(self):
        if self.ui:
            self.ui.showReprojectDemandPage()
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        return targetState in [DialogState.WELCOME, DialogState.LCOATIONSELECT, DialogState.REPROJECT]
    
    def setIsProcessing(self, value: bool) -> bool:
        self.context.set(ReprojectDemandHandler.KIsProcessing, value)

    def isProcessing(self) -> bool:
        return self.context.get(ReprojectDemandHandler.KIsProcessing, False)
    
    def getProcessing(self) -> Optional[Any]:
        return self.context.get(ReprojectDemandHandler.KProcessing)
    
    def setProcessing(self, value: Optional[Any]):
        self.context.set(ReprojectDemandHandler.KProcessing, value)
    
    def getProgress(self) -> RouteNetworkTaskProgress:
        return self.context.get(ReprojectDemandHandler.KProgress, RouteNetworkTaskProgress(0))
    
    def setProgress(self, value: RouteNetworkTaskProgress) -> RouteNetworkTaskProgress:
        return self.context.updateValue(ReprojectDemandHandler.KProgress, value, default=RouteNetworkTaskProgress(0))
    
    def getDetourTolerance(self) -> float:
        return self.context.get(ReprojectDemandHandler.KDetourTolerance, 1)
    
    def setDetourTolerance(self, value: float) -> float:
        return self.context.updateValue(ReprojectDemandHandler.KDetourTolerance, value)
    
    def getDemandFieldName(self) -> str:
        return self.context.get(ReprojectDemandHandler.KDemandFieldName, "")
    
    def setDemandFieldName(self, value: str) -> str:
        return self.context.updateValue(ReprojectDemandHandler.KDemandFieldName, value)

    def getNetworklayer(self) -> Optional[QgsVectorLayer]:
        return self.context.get(ReprojectDemandHandler.KNetworkLayer)
    
    def setNetworklayer(self, value: QgsVectorLayer) -> QgsVectorLayer:
        DialogState.deleteValuesAfterContext(DialogState.REPROJECTDEMAND, "LayerKeys")
        return self.context.updateValue(ReprojectDemandHandler.KNetworkLayer, value)
    
    def getPathfinder(self) -> Optional[NetworkPathFinder]:
        return self.context.get(ReprojectDemandHandler.KPathfinder)
    
    def setPathfinder(self, value: NetworkPathFinder) -> Optional[NetworkPathFinder]:
        return self.context.updateValue(ReprojectDemandHandler.KPathfinder, value)
    
    def getRouteLayer(self) -> Optional[RouteNetworklayer]:
        return self.context.get(ReprojectDemandHandler.KRouteLayer)
    
    def setRouteLayer(self, value: RouteNetworklayer) -> Optional[RouteNetworklayer]:
        DialogState.deleteValuesAfterContext(DialogState.REPROJECTDEMAND, "LayerKeys")
        return self.context.updateValue(ReprojectDemandHandler.KRouteLayer, value)
    
    def hasRouteLayer(self) -> bool:
        return self.context.has(ReprojectDemandHandler.KRouteLayer)
    
    def getSupplyNetworkLayer(self) -> Optional[SupplyNetworkElementLayer]:
        return self.context.get(ReprojectDemandHandler.KSupplyNetworkLayer)
    
    def setSupplyNetworkLayer(self, value: SupplyNetworkElementLayer) -> Optional[SupplyNetworkElementLayer]:
        DialogState.deleteValuesAfterContext(DialogState.REPROJECTDEMAND, "LayerKeys")
        return self.context.updateValue(ReprojectDemandHandler.KSupplyNetworkLayer, value)
    
    def hasSupplyNetworkLayer(self) -> bool:
        return self.context.has(ReprojectDemandHandler.KSupplyNetworkLayer)
    
    def setAggregatedSupplyNetworkLayer(self, value: SupplyAggregatedNetworkElementLayer) -> Optional[SupplyAggregatedNetworkElementLayer]:
        DialogState.deleteValuesAfterContext(DialogState.REPROJECTDEMAND, "LayerKeys")
        return self.context.updateValue(ReprojectDemandHandler.KAggregatedSupplyNetworkLayer, value)
    
    def setBreakingPointsNetworkLayer(self, value: BreakingPointsNetworkLayer) -> Optional[BreakingPointsNetworkLayer]:
        DialogState.deleteValuesAfterContext(DialogState.REPROJECTDEMAND, "LayerKeys")
        return self.context.updateValue(ReprojectDemandHandler.KBreakingPointsNetworkLayer, value)

    def setMissingRoutesLayer(self, value: MissingRoutesLayer) -> Optional[MissingRoutesLayer]:
        DialogState.deleteValuesAfterContext(DialogState.REPROJECTDEMAND, "LayerKeys")
        return self.context.updateValue(ReprojectDemandHandler.KMissingRoutesLayer, value)
    
    def setCenterDistanceTolerance(self, value: int) -> Optional[int]:
        return self.context.updateValue(ReprojectDemandHandler.KCenterDistanceTolerance, value)

class DialogState(Enum):
    """State machine enum with handlers"""
    WELCOME = WelcomeHandler()
    LCOATIONSELECT = LocationSelectHandler() 
    CENTERPOINTS = CenterPointsHandler()
    CENTERPOINTSEDIT = CenterPointsEditHandler()
    AIRLINE = AirlineHandler()
    REPROJECT = ReprojectHandler()
    REPROJECTDEMAND = ReprojectDemandHandler()
    
    def __init__(self, handler: StateHandler):
        self.handler = handler
    
    def enter(self, previousState: Optional['DialogState'] = None):
        """Enter this state"""
        self.handler.onEnter(previousState)
    
    def exit(self, nextState: Optional['DialogState'] = None):
        """Exit this state"""
        self.handler.onExit(nextState)
    
    def handleUi(self):
        """Handle UI for this state"""
        self.handler.handleUi()
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        """Check if we can transition to target state"""
        return self.handler.canTransitionTo(targetState)
    
    def isType(self, type: 'DialogState') -> bool:
        return self.name == type.name
    
    @staticmethod
    def context() -> 'DialogStateContext':
        return DialogState.WELCOME.value.getContext()
    
    @staticmethod
    def deleteValuesAfterContext(currentState: 'DialogState', keyAttributesName: str):
        kvs = DialogState.getValuesAfterContext(currentState, keyAttributesName)
    
        context = DialogState.context()
        for key in kvs.keys():
            context.delete(key)

    def getValuesAfterContext(currentState: 'DialogState', keyAttributesName: str) -> Dict[str, Any]:
        kvs = dict()
        states = list(DialogState)
        nextState = -1
        for (i, state) in enumerate(states):
            if state == currentState:
                nextState = i + 1
                break
        
        if nextState < 0:
            return kvs
        
        context = DialogState.context()
        for resetState in states[nextState:]:
            if hasattr(resetState.value, keyAttributesName):
                resetAttributeValues = getattr(resetState.value, keyAttributesName)
                for resetAttributevalue in resetAttributeValues:
                    value = context.get(resetAttributevalue)
                    if value:
                        kvs[resetAttributevalue] = value
        
        return kvs
    
    @property
    def name(self) -> str:
        return self.handler.name

class DialogStateContext:
    def __init__(self, initialState = DialogState.WELCOME):
        self._store = dict()
        self.currentState = initialState
    
    def setCurrentState(self, state: DialogState):
        self.currentState = state
    
    def clear(self):
        self._store.clear()
    
    def inner(self) -> Dict[str, Any]:
        return self._store
    
    def merge(self, other: Dict):
        self._store.update(other)
    
    def get(self, key: str, default: Any = None) -> Optional[Any]:
        if key in self._store:
            return self._store[key]
        else:
            return default
    
    def getOrSetDefault(self, key: str, default: Any) -> Any:
        if key in self._store:
            return self._store[key]
        else:
            self._store[key] = default
            return default
    
    def set(self, key: str, value: Any):
        self._store[key] = value
    
    def has(self, key: str) -> bool:
        return key in self._store and self._store[key] != None
    
    def updateValue(self, key: str, value: Any, default: Any = None) -> Optional[Any]:
        oldValue = default
        if key in self._store:
            oldValue = self._store[key]
        
        self._store[key] = value
        
        return oldValue
    
    def delete(self, key: str) -> Optional[Any]:
        if key in self._store:
            value = self._store[key]
            del self._store[key]
            return value
        else:
            return None
    
    def values(self):
        return self._store.values()

class DialogStateMachine:
    """State machine controller"""
    
    def __init__(self, initialState: DialogState, ui=None):
        self.ui = ui
        self.currentState = initialState
        self.context = DialogStateContext()
        self.stateHistory = [initialState]
        self.transitionCallbacks = {}
        
        # Set UI reference for all state handlers
        self.SetUiAndContextForAllStates()
        
        # Enter initial state
        self.currentState.enter(None)
    
    def SetUiAndContextForAllStates(self):
        """Set UI reference for all state handlers"""
        for state in DialogState:
            state.handler.setUi(self.ui)
            state.handler.setContext(self.context)
    
    def transitionTo(self, targetState: DialogState, **additionalContext) -> bool:
        """Transition to a new state"""
        if not self.currentState.canTransitionTo(targetState):
            print(f"Transition from {self.currentState.name} to {targetState.name} not allowed")
            return False
        
        print(f"\n--- Transitioning: {self.currentState.name} -> {targetState.name} ---")
        
        # Add any additional context
        self.context.merge(additionalContext)
        
        # Exit current state
        previousState = self.currentState
        self.currentState.exit(targetState)
        
        # Update current state
        self.currentState = targetState
        self.stateHistory.append(targetState)
        
        # Enter new state
        self.context.setCurrentState(targetState)
        self.currentState.enter(previousState)
        
        # Call transition callback if exists
        callbackKey = f"{previousState.name}To{targetState.name}"
        if callbackKey in self.transitionCallbacks:
            self.transitionCallbacks[callbackKey](self.context)
        
        return True
    
    def goBack(self) -> bool:
        """Go back to previous state"""
        if len(self.stateHistory) < 2:
            print("No previous state to return to")
            return False
        
        # Remove current state from history
        self.stateHistory.pop()
        previousState = self.stateHistory[-1]
        
        return self.transitionTo(previousState)
    
    def addTransitionCallback(self, fromState: DialogState, toState: DialogState, callback: Callable):
        """Add callback for specific state transition"""
        key = f"{fromState.name}To_{toState.name}"
        self.transitionCallbacks[key] = callback
    
    def getContext(self) -> Dict[str, Any]:
        """Get current context"""
        return self.context.copy()
    
    def updateContext(self, **kwargs):
        """Update context variables"""
        self.context.update(kwargs)
    
    def showCurrentUi(self):
        """Show UI for current state"""
        print(f"\n=== Current State: {self.currentState.name} ===")
        self.currentState.handleUi()
