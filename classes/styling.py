from qgis.PyQt.QtGui import QColor

from .network import LevelOfCentrality, ConnectivityFunction

class Colors:
    II = QColor("red")
    III = QColor("blue")
    IV = QColor("green")
    Extra = QColor("yellow")
    Surounding = QColor("orange")
    Default = QColor("gray")

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
            return 4
        elif loc == LevelOfCentrality.III:
            return 3
        elif loc == LevelOfCentrality.IV:
            return 2
        elif loc == LevelOfCentrality.Singular:
            return 3
        elif loc == LevelOfCentrality.Surounding:
            return 3
        else:
            return 1
    
    @staticmethod
    def getSizeForCF(cf: ConnectivityFunction):
        if cf == ConnectivityFunction.VFS_2:
            return 0.7
        elif cf == ConnectivityFunction.VFS_3:
            return 0.5
        elif cf == ConnectivityFunction.VFS_4:
            return 0.2
        elif cf == ConnectivityFunction.VFS_5:
            return 0.2
        else:
            return 0.2
