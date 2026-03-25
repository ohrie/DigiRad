from qgis.PyQt.QtGui import QColor

from qgis.core import (
    QgsSimpleLineSymbolLayer,
    QgsSymbol,
    QgsWkbTypes,
    Qgis
    )

from .network import LevelOfCentrality, ConnectivityFunction

class Colors:
    # Türkis
    II = QColor(67, 196, 155, 255)
    # Orange
    III = QColor(230, 159, 0, 255)
    # Blue
    IV = QColor(74, 164, 209, 255)
    # Pale Yellow
    Extra = QColor(255, 255, 191, 255)
    # Darker Orange
    Surounding = QColor(245, 124, 0, 255)
    Default = QColor("gray")
    # Magenta
    Error = QColor(255, 0, 255, 255) 

    Black = QColor("black")

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
            return 1.4
        elif cf == ConnectivityFunction.VFS_3:
            return 1.0
        elif cf == ConnectivityFunction.VFS_4:
            return 0.6
        elif cf == ConnectivityFunction.VFS_5:
            return 0.5
        else:
            return 0.5
    
    def getStyleForRouteLine(cf: ConnectivityFunction, isDemand: bool = False) -> QgsSymbol:
        if isDemand:
            symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
            symbol.deleteSymbolLayer(0)

            # --- Bottom layer: black dashed, wider ---
            baseLine = QgsSimpleLineSymbolLayer()
            baseLine.setColor(Colors.Black)
            baseLine.setWidth(Style.getSizeForCF(cf) + 0.4)
            baseLine.setUseCustomDashPattern(True)
            baseLine.setCustomDashVector([5, 3])
            baseLine.setCustomDashPatternUnit(Qgis.RenderUnit.Millimeters)

            # --- Top layer: normal solid line ---
            topLine = QgsSimpleLineSymbolLayer()
            topLine.setColor(Style.getColorForCF(cf))
            topLine.setWidth(Style.getSizeForCF(cf))
            topLine.setUseCustomDashPattern(True)
            topLine.setCustomDashVector([5, 3])
            topLine.setCustomDashPatternUnit(Qgis.RenderUnit.Millimeters)

            symbol.appendSymbolLayer(baseLine)
            symbol.appendSymbolLayer(topLine)
        else:
            symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
            symbol.setColor(Style.getColorForCF(cf))
            symbol.setWidth(Style.getSizeForCF(cf))

        return symbol
