from enum import Enum
from typing import Dict, Any, Optional, Set, Callable
from abc import ABC, abstractmethod

class StateHandler(ABC):
    """Base class for state handlers"""
    
    def __init__(self, name: str):
        self.name = name
        self.context_data = {}
    
    def setUi(self, ui):
        """Set the UI reference"""
        self.ui = ui
    
    @abstractmethod
    def onEnter(self, context: Dict[str, Any], previousState: Optional['DialogState'] = None):
        """Called when entering this state"""
        pass
    
    @abstractmethod
    def onExit(self, context: Dict[str, Any], nextState: Optional['DialogState'] = None):
        """Called when exiting this state"""
        pass
    
    @abstractmethod
    def handleUi(self, context: Dict[str, Any]):
        """Handle UI for this state"""
        pass
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        """Check if transition to target state is allowed"""
        return True

class WelcomeHandler(StateHandler):
    def __init__(self):
        super().__init__("Welcome")
    
    def onEnter(self, context: Dict[str, Any], previousState: Optional['DialogState'] = None):
        print(f"[LOGIN] Entering login state")
        if previousState:
            print(f"[LOGIN] Coming from: {previousState.name}")
        context['login_attempts'] = context.get('login_attempts', 0)
        self.handleUi(context)
    
    def onExit(self, context: Dict[str, Any], nextState: Optional['DialogState'] = None):
        print(f"[LOGIN] Exiting login state")
        if nextState:
            print(f"[LOGIN] Going to: {nextState.name}")
    
    def handleUi(self, context: Dict[str, Any]):
        if self.ui:
            self.ui.showWelcomePage(context)
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        return targetState == DialogState.LCOATIONSELECT

class LocationSelectHandler(StateHandler):
    def __init__(self):
        super().__init__("LocationSelect")
    
    def onEnter(self, context: Dict[str, Any], previousState: Optional['DialogState'] = None):
        print(f"[DASHBOARD] Entering dashboard state")
        if 'username' not in context:
            print("[DASHBOARD] Warning: No user logged in!")
        else:
            print(f"[DASHBOARD] Welcome, {context['username']}!")
        self.handleUi(context)
    
    def onExit(self, context: Dict[str, Any], nextState: Optional['DialogState'] = None):
        print(f"[DASHBOARD] Exiting dashboard state")
        # Store dashboard state
        context['last_dashboard_action'] = context.get('current_action', 'none')
    
    def handleUi(self, context: Dict[str, Any]):
        if self.ui:
            self.ui.showLocationSelectPage(context)
    
    def canTransitionTo(self, targetState):
        return targetState in [DialogState.WELCOME, DialogState.CENTERPOINTS]

class CenterPointsHandler(StateHandler):
    def __init__(self):
        super().__init__("CenterPoints")
    
    def onEnter(self, context: Dict[str, Any], previousState: Optional['DialogState'] = None):
        print(f"[WORK] Entering work area")
        context['workSessionStart'] = context.get('currentTime', 'unknown')
        # Transfer data from previous state
        if previousState and hasattr(previousState.value, 'context_data'):
            context.update(previousState.value.context_data)
        self.handleUi(context)
    
    def onExit(self, context: Dict[str, Any], nextState: Optional['DialogState'] = None):
        print(f"[WORK] Exiting work area")
        # Save work progress
        context['work_progress'] = context.get('tasksCompleted', 0)
    
    def handleUi(self, context: Dict[str, Any]):
        if self.ui:
            self.ui.showCenterPointsPage(context)
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        return targetState in [DialogState.LCOATIONSELECT, DialogState.CENTERPOINTSEDIT]

class CenterPointsEditHandler(StateHandler):
    def __init__(self):
        super().__init__("CenterPointsEdit")
    
    def onEnter(self, context: Dict[str, Any], previousState: Optional['DialogState'] = None):
        self.handleUi(context)
    
    def onExit(self, context: Dict[str, Any], nextState: Optional['DialogState'] = None):
        pass
    
    def handleUi(self, context: Dict[str, Any]):
        if self.ui:
            self.ui.showCenterPointsEditPage(context)
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        return targetState in [DialogState.CENTERPOINTS, DialogState.AIRLINE]

class AirlineHandler(StateHandler):
    def __init__(self):
        super().__init__("Airline")
    
    def onEnter(self, context: Dict[str, Any], previousState: Optional['DialogState'] = None):
        self.handleUi(context)
    
    def onExit(self, context: Dict[str, Any], nextState: Optional['DialogState'] = None):
        pass
    
    def handleUi(self, context: Dict[str, Any]):
        if self.ui:
            self.ui.showAirlinePage(context)
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        return targetState in [DialogState.CENTERPOINTSEDIT, DialogState.AIRLINEEDIT]

class AirlineEditHandler(StateHandler):
    def __init__(self):
        super().__init__("Airline")
    
    def onEnter(self, context: Dict[str, Any], previousState: Optional['DialogState'] = None):
        self.handleUi(context)
    
    def onExit(self, context: Dict[str, Any], nextState: Optional['DialogState'] = None):
        pass
    
    def handleUi(self, context: Dict[str, Any]):
        if self.ui:
            self.ui.showAirlineEditPage(context)
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        return targetState in [DialogState.AIRLINE, DialogState.REPROJECT]

class ReprojectHandler(StateHandler):
    def __init__(self):
        super().__init__("Airline")
    
    def onEnter(self, context: Dict[str, Any], previousState: Optional['DialogState'] = None):
        self.handleUi(context)
    
    def onExit(self, context: Dict[str, Any], nextState: Optional['DialogState'] = None):
        pass
    
    def handleUi(self, context: Dict[str, Any]):
        if self.ui:
            self.ui.showReprojectPage(context)
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        return targetState in [DialogState.AIRLINEEDIT]

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
    
    def enter(self, context: Dict[str, Any], previousState: Optional['DialogState'] = None):
        """Enter this state"""
        self.handler.onEnter(context, previousState)
    
    def exit(self, context: Dict[str, Any], nextState: Optional['DialogState'] = None):
        """Exit this state"""
        self.handler.onExit(context, nextState)
    
    def handleUi(self, context: Dict[str, Any]):
        """Handle UI for this state"""
        self.handler.handleUi(context)
    
    def canTransitionTo(self, targetState: 'DialogState') -> bool:
        """Check if we can transition to target state"""
        return self.handler.canTransitionTo(targetState)
    
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
        self.SetUiForAllStates()
        
        # Enter initial state
        self.currentState.enter(self.context)
    
    def SetUiForAllStates(self):
        """Set UI reference for all state handlers"""
        for state in DialogState:
            state.handler.setUi(self.ui)
    
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
        self.currentState.exit(self.context, targetState)
        
        # Update current state
        self.currentState = targetState
        self.stateHistory.append(targetState)
        
        # Enter new state
        self.currentState.enter(self.context, previousState)
        
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
        self.currentState.handleUi(self.context)