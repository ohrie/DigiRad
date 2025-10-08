from qgis.PyQt.QtGui import QColor

from .network import LevelOfCentrality, ConnectivityFunction

class Colors:
    # Red
    II = QColor(215, 25, 28, 255)
    # Orange
    III = QColor(253, 163, 78, 255)
    # Darker Blue
    IV = QColor(14, 84, 134, 255)
    # Pale Yellow
    Extra = QColor(255, 255, 191, 255)
    # Darker Orange
    Surounding = QColor(244,109,67, 255)
    Default = QColor("gray")
    # Magenta
    Error = QColor(255, 0, 255, 255) 

class Style:
    @staticmethod
    def getColorForLOC(loc: LevelOfCentrality):
        if loc == LevelOfCentrality.II:
            return Colors.II
        elif loc == LevelOfCentrality.III:
            return Colors.III
        elif loc == LevelOfCentrality.IV:
            return Colors.IV
        elif loc == LevelOfCentrality.Singular:
            return Colors.Extra
        elif loc == LevelOfCentrality.Surounding:
            return Colors.Surounding
        else:
            return Colors.Default
    
    @staticmethod
    def getColorForCF(cf: ConnectivityFunction):
        if cf == ConnectivityFunction.VFS_2:
            return Colors.II
        elif cf == ConnectivityFunction.VFS_3:
            return Colors.III
        elif cf == ConnectivityFunction.VFS_4:
            return Colors.IV
        elif cf == ConnectivityFunction.VFS_5:
            return Colors.Extra
        else:
            return Colors.Default
    
    @staticmethod
    def getSizeForLOC(loc: LevelOfCentrality):
        if loc == LevelOfCentrality.II:
            return 5
        elif loc == LevelOfCentrality.III:
            return 4
        elif loc == LevelOfCentrality.IV:
            return 3
        elif loc == LevelOfCentrality.Singular:
            return 4
        elif loc == LevelOfCentrality.Surounding:
            return 4
        else:
            return 1
    
    @staticmethod
    def getSizeForCF(cf: ConnectivityFunction):
        if cf == ConnectivityFunction.VFS_2:
            return 0.9
        elif cf == ConnectivityFunction.VFS_3:
            return 0.7
        elif cf == ConnectivityFunction.VFS_4:
            return 0.6
        elif cf == ConnectivityFunction.VFS_5:
            return 0.5
        else:
            return 0.5
