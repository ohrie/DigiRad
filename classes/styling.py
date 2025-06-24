from typing import Self
from qgis.PyQt.QtGui import QColor

from .network import LevelOfCentrality, ConnectivityFunction

class Colors:
    II = QColor("red")
    III = QColor("blue")
    IV = QColor("green")
    Extra = QColor("yellow")
    Default = QColor("gray")

class Style:
    @staticmethod
    def getColorForLOC(loc: LevelOfCentrality) -> QColor:
        match loc:
            case LevelOfCentrality.II:
                return Colors.II
            case LevelOfCentrality.III:
                return Colors.III
            case LevelOfCentrality.IV:
                return Colors.IV
            case LevelOfCentrality.Singular:
                return Colors.Extra
            case _:
                return Colors.Default
    
    @staticmethod
    def getColorForCF(cf: ConnectivityFunction) -> QColor:
        match cf:
            case ConnectivityFunction.VFS_2:
                return Colors.II
            case ConnectivityFunction.VFS_3:
                return Colors.III
            case ConnectivityFunction.VFS_4:
                return Colors.IV
            case ConnectivityFunction.VFS_5:
                return Colors.Extra
            case _:
                return Colors.Default
    
    @staticmethod
    def getSizeForLOC(loc: LevelOfCentrality) -> int:
        match loc:
            case LevelOfCentrality.II:
                return 4
            case LevelOfCentrality.III:
                return 3
            case LevelOfCentrality.IV:
                return 2
            case LevelOfCentrality.Singular:
                return 3
            case _:
                return 1
    
    @staticmethod
    def getSizeForCF(cf: ConnectivityFunction) -> int:
        match cf:
            case ConnectivityFunction.VFS_2:
                return 0.7
            case ConnectivityFunction.VFS_3:
                return 0.5
            case ConnectivityFunction.VFS_4:
                return 0.2
            case ConnectivityFunction.VFS_5:
                return 0.2
            case _:
                return 0.2
