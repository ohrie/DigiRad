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

from typing import List, Dict, Optional
from qgis.core import (
    QgsMessageLog,
    QgsVectorLayer,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsFeatureRequest,
    QgsPoint,
    QgsSymbol,
    QgsWkbTypes,
    QgsEditFormConfig,
    QgsAttributeEditorField,
    QgsEditorWidgetSetup
)

from ...constants import CRS_STR
from ..ars import ARSCodeStr
from .layer import DigiRadLayer
from ..network import LevelOfCentrality
from ..styling import Style

class CenterLayerFeatureConfig:
    def __init__(self, locName: str = "Zentralität", nameName: str = "Bemerkung", arsName: str = "ARS"):
        self.locName = locName
        self.nameName = nameName
        self.arsName = arsName

class CenterLayerFeature:
    def __init__(self, featureId, name: str, loc: LevelOfCentrality, geom: QgsPoint) -> 'CenterLayerFeature':
        self.featureId = featureId
        self.name = name
        self.loc = loc
        self.geom = geom

    @staticmethod
    def featuresFromLayer(layer: 'CenterLayer') -> Dict[LevelOfCentrality, List['CenterLayerFeature']]:
        qgsLayer = layer.qgsLayer()
        features = {}
        for loc in LevelOfCentrality:
            features[loc] = []
        
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
            geom = feat.geometry()
            if not geom:
                continue
            geom = geom.asPoint()
            geom = QgsPoint(geom.x(), geom.y())
            features[loc].append(CenterLayerFeature(feat.id(), name, loc, geom))

        return features

class CenterLayer(DigiRadLayer):
    LayerName = "Zentren"

    def __init__(self, layer, availableLOCs: List[LevelOfCentrality], config: CenterLayerFeatureConfig = CenterLayerFeatureConfig()):
        super().__init__(layer)
        self.config = config
        self.availableLOCs = availableLOCs
        renderer = self._createRenderer()
        formConfig = self._createFormConfig()
        filter = self._createFeatureFilter()
        layer.setEditFormConfig(formConfig)
        layer.setRenderer(renderer)
        layer.setSubsetString(filter)
        layer.triggerRepaint()

        self.locFeatures = CenterLayerFeature.featuresFromLayer(self)

    @staticmethod 
    def createEmpty(availableLOCs: Optional[List[LevelOfCentrality]] = LevelOfCentrality.defaults(), config: CenterLayerFeatureConfig = CenterLayerFeatureConfig()) -> 'CenterLayer':
        layer = QgsVectorLayer("Point?crs={}&field={}:string&field={}:string".format(config.nameName, config.locName, CRS_STR), CenterLayer.LayerName, "memory")
        return CenterLayer(layer, availableLOCs)

    @staticmethod
    def loadFromFile(filePath: str, arsCodeStr: ARSCodeStr = ARSCodeStr.empty(), availableLOCs: Optional[List[LevelOfCentrality]] = LevelOfCentrality.defaults(), config: CenterLayerFeatureConfig = CenterLayerFeatureConfig()):
        layer = QgsVectorLayer(filePath, CenterLayer.LayerName, "ogr")

        if arsCodeStr.isEmpty():
            request = QgsFeatureRequest()
        else:
            relevantCodePart = arsCodeStr.getRelevantPart()
            request = QgsFeatureRequest().setFilterExpression("substr(\"{}\", 1, {}) = '{}'".format(config.arsName, len(relevantCodePart), relevantCodePart))
        
        layer = layer.materialize(request)
        return CenterLayer(layer, availableLOCs, config)
    
    def update(self):
        self.locFeatures = CenterLayerFeature.featuresFromLayer(self)
    
    def _createRenderer(self) -> QgsCategorizedSymbolRenderer:
        renderer = QgsCategorizedSymbolRenderer(self.config.locName)
        
        for loc in self.availableLOCs:
            symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PointGeometry)
            symbol.setColor(Style.getColorForLOC(loc))
            symbol.setSize(Style.getSizeForLOC(loc))
            cat = QgsRendererCategory(loc.asStrShort(), symbol, loc.asStr())

            renderer.addCategory(cat)

        return renderer
    
    def _createFormConfig(self):
        formConfig = QgsEditFormConfig()
        formConfig.setLayout(QgsEditFormConfig.TabLayout)
        root = formConfig.invisibleRootContainer()
        layer = self.qgsLayer()
        fields = layer.fields()

        locIdx = fields.indexFromName(self.config.locName)
        if locIdx >= 0:
            locElement = QgsAttributeEditorField(self.config.locName, locIdx, None)
            root.addChildElement(locElement)

            valueMap = {}
            for loc in self.availableLOCs:
                valueMap[loc.asStr()] = loc.asStrShort()
            
            widgetSetup = QgsEditorWidgetSetup('ValueMap', {
                'map': valueMap,
                'AllowMulti': False,
                'AllowNull': False
            })
            layer.setEditorWidgetSetup(locIdx, widgetSetup)
        
        nameIdx = fields.indexFromName(self.config.nameName)
        if nameIdx >= 0:
            nameElement = QgsAttributeEditorField(self.config.nameName, nameIdx, None)
            root.addChildElement(nameElement)
            
            widgetSetup = QgsEditorWidgetSetup('TextEdit', {'IsMultiline': False, 'Readonly': True})
            layer.setEditorWidgetSetup(nameIdx, widgetSetup)
        
        return formConfig
    
    def _createFeatureFilter(self) -> str:
        locs = ", ".join(map(lambda loc: "'{}'".format(loc.asStrShort()), self.availableLOCs))
        return "{} in ({})".format(self.config.locName, locs)