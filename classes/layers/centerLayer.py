# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CenterLayer
                                 A QGIS plugin
 Unterstützung bei der Erstellung von digitalen Angebotsnetzen für den Radverkehr
                             -------------------
        begin                : 2025-05-13
        git sha              : $Format:%H$
        copyright            : (C) 2025 by Vision Velo UG (haftungsbeschränkt)
        email                : info@vision-velo.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from typing import Self, List, Dict
from qgis.core import QgsMessageLog, QgsVectorLayer, QgsCategorizedSymbolRenderer, QgsMarkerSymbol, QgsRendererCategory, QgsFeatureRequest, QgsPoint

from ..network import LevelOfCentrality

class CenterLayerFeatureConfig:
    def __init__(self, locName: str = "loc", nameName: str = "name"):
        self.locName = locName
        self.nameName = nameName

class CenterLayerFeature:
    def __init__(self, featureId, name: str, loc: LevelOfCentrality, geom: QgsPoint) -> Self:
        self.featureId = featureId
        self.name = name
        self.loc = loc
        self.geom = geom

    @staticmethod
    def featuresFromLayer(layer) -> Dict[LevelOfCentrality, List[Self]]:
        qgsLayer = layer.qgsLayer()
        features = {
            LevelOfCentrality.GRUNDZENTRUM: [],
            LevelOfCentrality.MITTELZENTRUM: [],
            LevelOfCentrality.OBERZENTRUM: [],
        }
        
        nameIdx = qgsLayer.fields().indexFromName(layer.config.nameName)
        locIdx = qgsLayer.fields().indexFromName(layer.config.locName)
        request = QgsFeatureRequest()
        request.setSubsetOfAttributes([locIdx, nameIdx])
        for feat in qgsLayer.getFeatures(request):
            name = feat.attributes()[nameIdx]
            loc = feat.attributes()[locIdx]
            try:
                loc = LevelOfCentrality.fromStr(loc)
            except Exception as e:
                QgsMessageLog.logMessage(f"Unable to get level of centrality for feature {feat.id()} ({name}): {e}")
                continue
            geom = feat.geometry().asPoint()
            geom = QgsPoint(geom.x(), geom.y())
            features[loc].append(CenterLayerFeature(feat.id(), name, loc, geom))

        return features

class CenterLayer():
    def __init__(self, layer, config: CenterLayerFeatureConfig = CenterLayerFeatureConfig()):
        renderer = self._createRenderer(config.locName)
        layer.setRenderer(renderer)
        layer.triggerRepaint()

        self._layer = layer
        self.config = config
        self.locFeatures = CenterLayerFeature.featuresFromLayer(self)
    
    @staticmethod
    def loadFromFile(filePath: str, layerName):
        layer = QgsVectorLayer(filePath, layerName, "ogr")
        return CenterLayer(layer)
    
    def _createRenderer(self, categoryField: str) -> QgsCategorizedSymbolRenderer:
        renderer = QgsCategorizedSymbolRenderer(categoryField)

        categories = [
            [LevelOfCentrality.OBERZENTRUM.asStr(), QgsMarkerSymbol.createSimple({'color': '0,0,255', 'size': '4'}), LevelOfCentrality.OBERZENTRUM.asStr()],
            [LevelOfCentrality.MITTELZENTRUM.asStr(), QgsMarkerSymbol.createSimple({'color': '0,255,0', 'size': '3'}), LevelOfCentrality.MITTELZENTRUM.asStr()],
            [LevelOfCentrality.GRUNDZENTRUM.asStr(), QgsMarkerSymbol.createSimple({'color': '255,0,0', 'size': '2'}), LevelOfCentrality.GRUNDZENTRUM.asStr()],
        ]

        for category in categories:
            value = category[0]
            symbol = category[1]
            label = category[2]
            
            cat = QgsRendererCategory(value, symbol, label)
            renderer.addCategory(cat)
        
        return renderer
    

    def qgsLayer(self):
        return self._layer
    
    def name(self):
        return self._layer.name()