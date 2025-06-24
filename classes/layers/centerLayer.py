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
from qgis.core import (
    QgsMessageLog,
    QgsVectorLayer,
    QgsCategorizedSymbolRenderer,
    QgsMarkerSymbol,
    QgsRendererCategory,
    QgsFeatureRequest,
    QgsPoint,
    QgsSymbol,
    QgsWkbTypes,
    QgsEditFormConfig,
    QgsAttributeEditorField,
    QgsEditorWidgetSetup
)

from .layer import DigiRadLayer
from ..network import LevelOfCentrality
from ..styling import Colors

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
    def featuresFromLayer(layer: 'CenterLayer') -> Dict[LevelOfCentrality, List[Self]]:
        qgsLayer = layer.qgsLayer()
        features = {
            LevelOfCentrality.IV: [],
            LevelOfCentrality.III: [],
            LevelOfCentrality.II: [],
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
            geom = feat.geometry()
            if not geom:
                continue
            geom = geom.asPoint()
            geom = QgsPoint(geom.x(), geom.y())
            features[loc].append(CenterLayerFeature(feat.id(), name, loc, geom))

        return features

class CenterLayer(DigiRadLayer):
    def __init__(self, layer, config: CenterLayerFeatureConfig = CenterLayerFeatureConfig()):
        super().__init__(layer)
        self.config = config
        renderer = self._createRenderer()
        formConfig = self._createFormConfig()
        layer.setEditFormConfig(formConfig)
        layer.setRenderer(renderer)
        layer.triggerRepaint()

        self.locFeatures = CenterLayerFeature.featuresFromLayer(self)

    
    @staticmethod 
    def createEmpty() -> Self:
        layer = QgsVectorLayer("Point?crs=EPSG:3857&field=name:string&field=loc:string", "Zentren", "memory")
        return CenterLayer(layer)

    @staticmethod
    def loadFromFile(filePath: str, layerName):
        layer = QgsVectorLayer(filePath, layerName, "ogr")
        return CenterLayer(layer)
    
    def update(self):
        self.locFeatures = CenterLayerFeature.featuresFromLayer(self)
    
    def _createRenderer(self) -> QgsCategorizedSymbolRenderer:
        renderer = QgsCategorizedSymbolRenderer(self.config.locName)

        categories = [
            [LevelOfCentrality.II.asStr(), Colors.II, 4],
            [LevelOfCentrality.III.asStr(), Colors.III, 3],
            [LevelOfCentrality.IV.asStr(), Colors.IV, 2],
        ]

        for category in categories:
            symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PointGeometry)
            symbol.setColor(category[1])
            symbol.setSize(category[2])
            cat = QgsRendererCategory(category[0], symbol, category[0])

            renderer.addCategory(cat)
        
        return renderer
    
    def _createFormConfig(self):
        formConfig = QgsEditFormConfig()
        formConfig.setLayout(QgsEditFormConfig.TabLayout)
        root = formConfig.invisibleRootContainer()
        layer = self.qgsLayer()
        fields = layer.fields()

        nameIdx = fields.indexFromName(self.config.nameName)
        if nameIdx >= 0:
            nameElement = QgsAttributeEditorField(self.config.nameName, nameIdx, None)
            root.addChildElement(nameElement)
            
            # Make it read-only by changing its widget type
            widgetSetup = QgsEditorWidgetSetup('TextEdit', {'IsMultiline': False, 'Readonly': True})
            layer.setEditorWidgetSetup(nameIdx, widgetSetup)

        # 5. Add type field as a combo box with predefined values
        locIdx = fields.indexFromName(self.config.locName)
        if locIdx >= 0:
            locElement = QgsAttributeEditorField(self.config.locName, locIdx, None)
            root.addChildElement(locElement)
            
            # Configure as ValueMap (combo box) with predefined values
            valueMap = {
                LevelOfCentrality.II.asStr(): LevelOfCentrality.II.asStr(),
                LevelOfCentrality.III.asStr(): LevelOfCentrality.III.asStr(),
                LevelOfCentrality.IV.asStr(): LevelOfCentrality.IV.asStr(),
            }
            widgetSetup = QgsEditorWidgetSetup('ValueMap', {
                'map': valueMap,
                'AllowMulti': False,
                'AllowNull': False
            })
            layer.setEditorWidgetSetup(locIdx, widgetSetup)
        
        return formConfig
    