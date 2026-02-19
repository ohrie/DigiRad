from PyQt5.QtCore import QObject, QEvent, Qt, pyqtSignal

from qgis.core import QgsMessageLog

from ...dialogstate import DialogStateMachine, DialogState

class KeyPressFilter(QObject):
    centerEditEscape = pyqtSignal()

    def __init__(self, state: DialogStateMachine):
        super().__init__()
        self.state = state

    def eventFilter(self, obj, event):
        # Check if escape was pressed while in state CENTERPOINTSEDIT
        # If so, emit centerEditEscape signal
        if self.state.currentState == DialogState.CENTERPOINTSEDIT:
            if not event or not event.type():
                return False # let event continue
            if event.type() == QEvent.Type.KeyRelease and event.key():
                if event.key() == Qt.Key_Escape:
                    self.centerEditEscape.emit()
                    return True  # stop propagation (optional)

        return False  # let event continue