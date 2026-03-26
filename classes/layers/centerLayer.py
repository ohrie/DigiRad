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
    QgsFeature,
    QgsGeometry,
    QgsPoint,
    QgsPointXY,
    QgsRectangle,
    QgsSymbol,
    QgsMarkerSymbol,
    QgsWkbTypes,
    QgsEditFormConfig,
    QgsAttributeEditorField,
    QgsEditorWidgetSetup
)

from ...constants import CRS_STR, SUROUNDING_QUERY_DISTANCE
from ...constants import SUROUNDING_LAYER 
from ..ars import ARSCodeStr
from .layer import DigiRadLayer
from ..network import LevelOfCentrality
from ..styling import Style
from .centerLayerFeatures import CenterLayerFeature, CenterLayerFeatureConfig
from ..processing.meshCalculator import MeshCalculator

class CenterLayer(DigiRadLayer):
    LayerName = "Zentren"

    def __init__(self, layer, arsCodeStr: ARSCodeStr, config: CenterLayerFeatureConfig = CenterLayerFeatureConfig()):
        super().__init__(layer)
        self.arsCodeStr = arsCodeStr
        self.config = config
        renderer = self._createRenderer()
        formConfig = self._createFormConfig()
        layer.setEditFormConfig(formConfig)
        layer.setRenderer(renderer)
        layer.triggerRepaint()

        self.locFeatures = CenterLayerFeature.featuresFromLayer(layer, config)

    @staticmethod
    def createEmpty(arsCodeStr: ARSCodeStr = ARSCodeStr.empty(), config: CenterLayerFeatureConfig = CenterLayerFeatureConfig()) -> 'CenterLayer':
        layer = QgsVectorLayer("Point?crs={}&field={}:string&field={}:string".format(config.nameName, config.locName, CRS_STR), CenterLayer.LayerName, "memory")
        return CenterLayer(layer, arsCodeStr)

    @staticmethod
    def loadFromFile(filePath: str, arsCodeStr: ARSCodeStr = ARSCodeStr.empty(), filterLOCs: Optional[List[LevelOfCentrality]] = LevelOfCentrality.defaults(), config: CenterLayerFeatureConfig = CenterLayerFeatureConfig()):
        layer = QgsVectorLayer(filePath, CenterLayer.LayerName, "ogr")

        return CenterLayer.loadFromLayer(layer, arsCodeStr, filterLOCs, config)
    
    @staticmethod
    def loadFromLayer(layer: QgsVectorLayer, arsCodeStr: ARSCodeStr = ARSCodeStr.empty(), filterLOCs: Optional[List[LevelOfCentrality]] = LevelOfCentrality.defaults(), config: CenterLayerFeatureConfig = CenterLayerFeatureConfig()):
        filter = CenterLayer._createFeatureFilter(config, arsCodeStr, filterLOCs)
        request = QgsFeatureRequest().setFilterExpression(filter)

        layer = layer.materialize(request)
        # If there is no ARSCodeStr, we cannot get plausible suroundings 
        if not arsCodeStr.isEmpty():
            layer = CenterLayer._mergeWithSuroundings(arsCodeStr, layer, config)
        
        return CenterLayer(layer, arsCodeStr, config)
    
    @staticmethod
    def _mergeWithSuroundings(arsCodeStr: ARSCodeStr, layer: QgsVectorLayer, config: CenterLayerFeatureConfig) -> QgsVectorLayer:
        suroundingFeats = SuroundingHelper.getSuroundingFeatures(arsCodeStr, layer, config)

        # Get next free feature id of the loc layer
        fidIdx = layer.fields().indexFromName("fid")
        maxFeatId = 0
        for feat in layer.getFeatures():
            fid = feat[fidIdx]
            if fid > maxFeatId:
                maxFeatId = fid
        
        maxFeatId += 1

        pr = layer.dataProvider()
        feats = []
        for centerFeat in suroundingFeats:
            feat = QgsFeature()
            feat.setAttributes([maxFeatId, "", centerFeat.name, centerFeat.loc.asStrShort()])
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(centerFeat.geom.x(), centerFeat.geom.y())))
            feats.append(feat)
            maxFeatId += 1

        pr.addFeatures(feats)
        layer.updateExtents()
        
        return layer
    
    def update(self):
        self.locFeatures = CenterLayerFeature.featuresFromLayer(self.qgsLayer(), self.config)
    
    def _createRenderer(self) -> QgsCategorizedSymbolRenderer:
        renderer = QgsCategorizedSymbolRenderer(self.config.locName)
        
        for loc in LevelOfCentrality:
            if loc == LevelOfCentrality.Surounding:
                symbol = QgsMarkerSymbol.createSimple({'name': 'diamond'})
            else:
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
            for loc in LevelOfCentrality:
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
    
    @staticmethod
    def _createFeatureFilter(config: CenterLayerFeatureConfig, arsCodeStr: ARSCodeStr, filterLocs: List[LevelOfCentrality]) -> str:
        locFilter = "{} in ({})".format(config.locName, ", ".join(map(lambda loc: "'{}'".format(loc.asStrShort()), filterLocs)))
        if arsCodeStr.isEmpty():
           return locFilter
         
        relevantCodePart = arsCodeStr.getRelevantPart()
        arsFilter = "substr(\"{}\", 1, {}) = '{}'".format(config.arsName, len(relevantCodePart), relevantCodePart)

        QgsMessageLog.logMessage(f"{arsFilter} AND {locFilter}")
        return f"{arsFilter} AND {locFilter}"

class SuroundingHelper:

    @staticmethod
    def getSuroundingFeatures(arsCodeStr: ARSCodeStr, centerLayer: QgsVectorLayer, config: CenterLayerFeatureConfig) -> List[CenterLayerFeature]:
        featureBounds = centerLayer.extent()
        queryBounds = QgsRectangle(
            featureBounds.xMinimum() - SUROUNDING_QUERY_DISTANCE,
            featureBounds.yMinimum() - SUROUNDING_QUERY_DISTANCE,
            featureBounds.xMaximum() + SUROUNDING_QUERY_DISTANCE,
            featureBounds.yMaximum() + SUROUNDING_QUERY_DISTANCE
            )
        request = QgsFeatureRequest().setFilterRect(queryBounds).setFlags(QgsFeatureRequest.ExactIntersect)
        locFeatures = CenterLayerFeature.featuresFromLayer(centerLayer, config)
        
        suroundingFeats = []
        arsIdx = SUROUNDING_LAYER.fields().indexFromName("ARS_2")
        nameIdx = SUROUNDING_LAYER.fields().indexFromName("GEN")
        for feat in SUROUNDING_LAYER.getFeatures(request):
            ars = feat[arsIdx]
            # Skip ars of self
            if arsCodeStr.code == ars:
                continue

            name = feat[nameIdx]
            geom = feat.geometry().asPoint()
            geom = QgsPoint(geom.x(), geom.y())
            
            suroundingFeats.append(
                CenterLayerFeature(feat.id(), name, LevelOfCentrality.Surounding, geom))
        
        allFeats = suroundingFeats
        for locFeats in locFeatures.values():
            allFeats += locFeats
        
        meshCalc = MeshCalculator()
        directRoutes = meshCalc.extractDirectRoutes(allFeats)
        nearbySuroundingFeats = []
        nearbyAddedIds = set()
        for route in directRoutes.values():
            if route.feat1.loc == LevelOfCentrality.Surounding:
                if route.feat2.loc != LevelOfCentrality.Surounding and route.feat1.featureId not in nearbyAddedIds:
                    nearbySuroundingFeats.append(route.feat1)
                    nearbyAddedIds.add(route.feat1.featureId)
            elif route.feat2.loc == LevelOfCentrality.Surounding:
                if route.feat1.loc != LevelOfCentrality.Surounding and route.feat2.featureId not in nearbyAddedIds:
                    nearbySuroundingFeats.append(route.feat2)
                    nearbyAddedIds.add(route.feat2.featureId)
        
        return nearbySuroundingFeats