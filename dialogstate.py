from enum import Enum
from typing import Dict, Any, Optional, Set, Callable, List
from abc import ABC, abstractmethod

from .classes.network import LevelOfCentrality, ConnectivityFunction
from .classes.layers.centerLayer import CenterLayer
from .classes.processing.directRouteNetwork import DirectRouteGenerateMethod
from .classes.processing.routeNetworkTask import RouteNetworkTask

class StateHandler(ABC):
    """Base class for state handlers"""
    
    def __init__(self, name: str):
        self.name = name
        self.context_data = {}
        self.context = {}
    
    def setUi(self, ui):
        """Set the UI reference"""
        self.ui = ui
    
    def setContext(self, context: Dict[str, Any]):
        """Set the context reference"""
        self.context = context
    
    def _updateValue(self, value, key: str, default: Any = None) -> Any:
        oldValue = default
        if key in self.context:
            oldValue = self.context[key]
        
        self.context[key] = value
        
        return oldValue
    
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
        print(f"[LOGIN] Entering login state")
        if previousState:
            print(f"[LOGIN] Coming from: {previousState.name}")
        self.context['login_attempts'] = self.context.get('login_attempts', 0)
        self.handleUi()
    
    def onExit(self, nextState: Optional['DialogState'] = None):
        print(f"[LOGIN] Exiting login state")
        if nextState:
            print(f"[LOGIN] Going to: {nextState.name}")
    
    def handleUi(self):
        if self.ui:
            self.ui.showWelcomePage()
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        return targetState == DialogState.LCOATIONSELECT

class LocationSelectHandler(StateHandler):
    def __init__(self):
        super().__init__("LocationSelect")
    
    def onEnter(self, previousState: Optional['DialogState'] = None):
        # print(f"[DASHBOARD] Entering dashboard state")
        # if 'username' not in context:
        #     print("[DASHBOARD] Warning: No user logged in!")
        # else:
        #     print(f"[DASHBOARD] Welcome, {context['username']}!")
        self.handleUi()
    
    def onExit(self, nextState: Optional['DialogState'] = None):
        pass
        # print(f"[DASHBOARD] Exiting dashboard state")
        # # Store dashboard state
        # context['last_dashboard_action'] = context.get('current_action', 'none')
    
    def handleUi(self):
        if self.ui:
            self.ui.showLocationSelectPage()
    
    def canTransitionTo(self, targetState):
        return targetState in [DialogState.WELCOME, DialogState.CENTERPOINTS]

class CenterPointsHandler(StateHandler):
    KCenterLayer = "center.CenterLayer"
    KGenerateMethod = "center.GenerateMethod"
    KLOCs = "center.LOCs"

    def __init__(self):
        super().__init__("CenterPoints")
    
    def onEnter(self, previousState: Optional['DialogState'] = None):
        # print(f"[WORK] Entering work area")
        # context['workSessionStart'] = context.get('currentTime', 'unknown')
        # # Transfer data from previous state
        # if previousState and hasattr(previousState.value, 'context_data'):
        #     context.update(previousState.value.context_data)
        self.handleUi()
    
    def onExit(self, nextState: Optional['DialogState'] = None):
        pass
        # print(f"[WORK] Exiting work area")
        # # Save work progress
        # context['work_progress'] = context.get('tasksCompleted', 0)
    
    def handleUi(self):
        if self.ui:
            self.ui.showCenterPointsPage()
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        return targetState in [DialogState.LCOATIONSELECT, DialogState.CENTERPOINTSEDIT]
    
    def hasCenterLayer(self) -> bool:
        return CenterPointsHandler.KCenterLayer in self.context
    
    def getCenterLayer(self) -> Optional[CenterLayer]:
        if CenterPointsHandler.KCenterLayer in self.context:
            return self.context[CenterPointsHandler.KCenterLayer]
        else:
            return None
    
    def setCenterLayer(self, value: CenterLayer) -> Optional[CenterLayer]:
        oldValue = None
        if CenterPointsHandler.KCenterLayer in self.context:
            oldValue = self.context[CenterPointsHandler.KCenterLayer]
        
        self.context[CenterPointsHandler.KCenterLayer] = value
        
        # Update the UI
        self.handleUi()

        return oldValue
    
    def getGenerateMethod(self) -> DirectRouteGenerateMethod:
        if CenterPointsHandler.KGenerateMethod not in self.context:
            self.context[CenterPointsHandler.KGenerateMethod] = DirectRouteGenerateMethod.default()
    
        return self.context[CenterPointsHandler.KGenerateMethod]
    
    def setGenerateMethod(self, value: DirectRouteGenerateMethod) -> Optional[DirectRouteGenerateMethod]:
        return self._updateValue(value, CenterPointsHandler.KGenerateMethod, default=DirectRouteGenerateMethod.default())
    
    def getLOCS(self) -> List[LevelOfCentrality]:
        if CenterPointsHandler.KLOCs not in self.context:
            self.context[CenterPointsHandler.KLOCs] = LevelOfCentrality.defaults()
    
        return self.context[CenterPointsHandler.KLOCs]
    
    def setLOCs(self, value: List[LevelOfCentrality]) -> Optional[List[LevelOfCentrality]]:
        return self._updateValue(value, CenterPointsHandler.KLOCs, default=LevelOfCentrality.defaults())

class CenterPointsEditHandler(StateHandler):
    def __init__(self):
        super().__init__("CenterPointsEdit")
    
    def onEnter(self, previousState: Optional['DialogState'] = None):
        self.handleUi()
    
    def onExit(self, nextState: Optional['DialogState'] = None):
        pass
    
    def handleUi(self):
        if self.ui:
            self.ui.showCenterPointsEditPage()
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        return targetState in [DialogState.CENTERPOINTS, DialogState.AIRLINE]

class AirlineHandler(StateHandler):
    KCFs = "airline.CFs"

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
        return targetState in [DialogState.CENTERPOINTSEDIT, DialogState.AIRLINEEDIT]
    
    def hasCFs(self) -> bool:
        return AirlineHandler.KCFs in self.context
    
    def getCFs(self) -> List[ConnectivityFunction]:
        if AirlineHandler.KCFs not in self.context:
            self.context[AirlineHandler.KCFs] = ConnectivityFunction.defaults()
    
        return self.context[AirlineHandler.KCFs]
    
    def setCFs(self, value: List[ConnectivityFunction]) -> List[ConnectivityFunction]:
        return self._updateValue(value, AirlineHandler.KCFs, default=ConnectivityFunction.defaults())

class AirlineEditHandler(StateHandler):
    def __init__(self):
        super().__init__("Airline")
    
    def onEnter(self, previousState: Optional['DialogState'] = None):
        self.handleUi()
    
    def onExit(self, nextState: Optional['DialogState'] = None):
        pass
    
    def handleUi(self):
        if self.ui:
            self.ui.showAirlineEditPage()
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        return targetState in [DialogState.AIRLINE, DialogState.REPROJECT]

class ReprojectHandler(StateHandler):
    KProcessing = "reproject.Processing"
    KProgress = "reproject.Progress"

    def __init__(self):
        super().__init__("Airline")
    
    def onEnter(self, previousState: Optional['DialogState'] = None):
        self.handleUi()
    
    def onExit(self, nextState: Optional['DialogState'] = None):
        pass
    
    def handleUi(self):
        if self.ui:
            self.ui.showReprojectPage()
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        return targetState in [DialogState.AIRLINEEDIT]
    
    def isProcessing(self) -> bool:
        if ReprojectHandler.KProcessing in self.context:
            return self.context[ReprojectHandler.KProcessing] != None
        else:
            return False
    
    def getProcessing(self) -> Optional[RouteNetworkTask]:
        if ReprojectHandler.KProcessing in self.context:
            return self.context[ReprojectHandler.KProcessing]
        else:
            return None
    
    def setProcessing(self, value: Optional[RouteNetworkTask]):
        self.context[ReprojectHandler.KProcessing] = value
    
    def getProgress(self) -> int:
        if ReprojectHandler.KProgress in self.context:
            return self.context[ReprojectHandler.KProgress]
        else:
            return 0
    
    def setProgress(self, value: int) -> int:
        return self._updateValue(value, ReprojectHandler.KProgress, default=0)


class DialogState(Enum):
    """State machine enum with handlers"""
    WELCOME = WelcomeHandler()
    LCOATIONSELECT = LocationSelectHandler() 
    CENTERPOINTS = CenterPointsHandler()
    CENTERPOINTSEDIT = CenterPointsEditHandler()
    AIRLINE = AirlineHandler()
    AIRLINEEDIT = AirlineEditHandler()
    REPROJECT = ReprojectHandler()
    
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
    
    @property
    def name(self) -> str:
        return self.handler.name

class DialogStateMachine:
    """State machine controller"""
    
    def __init__(self, initialState: DialogState, ui=None):
        self.ui = ui
        self.currentState = initialState
        self.context = {}
        self.stateHistory = [initialState]
        self.transitionCallbacks = {}
        
        # Set UI reference for all state handlers
        self.SetUiAndContextForAllStates()
        
        # Enter initial state
        self.currentState.enter(self.context)
    
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
        self.context.update(additionalContext)
        
        # Exit current state
        previousState = self.currentState
        self.currentState.exit(targetState)
        
        # Update current state
        self.currentState = targetState
        self.stateHistory.append(targetState)
        
        # Enter new state
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