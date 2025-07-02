# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AnalysisLayers
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
from typing import List

from PyQt5.QtCore import QVariant
from qgis.core import (
    QgsMessageLog,
    QgsVectorLayer,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsField,
    QgsSymbol,
    QgsMarkerSymbol,
    QgsWkbTypes,
    QgsFeatureRequest,
    )

from .layer import DigiRadLayer
from ..network import ConnectivityFunction
from ..processing.routeNetworkAnalyser import NetworkElement, AggregatedNetworkElement, BreakingElement
from ..styling import Style

class SupplyNetworkElemenFeatureConfig:
    def __init__(self, edgeIdName: str = "KantenId", cfName: str = "Verbindungsfunktionsstufe", occupancyName: str = "Belegung") -> 'SupplyNetworkElemenFeatureConfig':
        self.edgeIdName = edgeIdName
        self.cfName = cfName
        self.occupancyName = occupancyName
        self.occupancyNameCF2 = "{} {}".format(occupancyName, ConnectivityFunction.VFS_2.asStrShort())
        self.occupancyNameCF3 = "{} {}".format(occupancyName, ConnectivityFunction.VFS_3.asStrShort())
        self.occupancyNameCF4 = "{} {}".format(occupancyName, ConnectivityFunction.VFS_4.asStrShort())

class SupplyNetworkElementLayer(DigiRadLayer):
    LayerName = "Angebotsnetz"

    def __init__(self, networkElements: List[NetworkElement], config: SupplyNetworkElemenFeatureConfig = SupplyNetworkElemenFeatureConfig()) -> 'SupplyNetworkElementLayer':
        super().__init__(
            SupplyNetworkElementLayer._createLayerFromNetworkElements(networkElements, config),
            "Umlegung",
            expanded=False,
            visible=False
        )

        self.networkElements = networkElements
        self.config = config

        renderer = self._createRenderer()
        self._qgsLayer.setRenderer(renderer)
        self._qgsLayer.triggerRepaint()

    @staticmethod
    def _createLayerFromNetworkElements(networkElements: List[NetworkElement], config: SupplyNetworkElemenFeatureConfig) -> QgsVectorLayer:
        routeLayer = QgsVectorLayer("LineString?crs=EPSG:3857", 
                             SupplyNetworkElementLayer.LayerName, "memory")
        pr = routeLayer.dataProvider()
        pr.addAttributes([
            QgsField(config.edgeIdName, QVariant.LongLong),
            QgsField(config.cfName, QVariant.String),
            QgsField(config.occupancyName , QVariant.Int),
            QgsField(config.occupancyNameCF2, QVariant.Int),
            QgsField(config.occupancyNameCF3, QVariant.Int),
            QgsField(config.occupancyNameCF4, QVariant.Int),
        ])
        routeLayer.updateFields()
        features = []
        for element in networkElements:
            features.append(element.toQgsFeature())
        pr.addFeatures(features)

        routeLayer.updateExtents()

        return routeLayer
    
    def _createRenderer(self) -> QgsCategorizedSymbolRenderer:
        renderer = QgsCategorizedSymbolRenderer(self.config.cfName)

        for cf in [ConnectivityFunction.VFS_2, ConnectivityFunction.VFS_3, ConnectivityFunction.VFS_4]:
            symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
            symbol.setColor(Style.getColorForCF(cf))
            symbol.setWidth(Style.getSizeForCF(cf))
            cat = QgsRendererCategory(cf.asStrShort(), symbol, cf.asStr())

            renderer.addCategory(cat)
        
        orderBy = QgsFeatureRequest.OrderBy([QgsFeatureRequest.OrderByClause(self.config.cfName, False)])
        renderer.setOrderByEnabled(True)
        renderer.setOrderBy(orderBy)
        
        return renderer

class SupplyAggregatedNetworkElementLayer(DigiRadLayer):
    LayerName = "Angebotsnetz (aggregiert)"

    def __init__(self, networkElements: List[AggregatedNetworkElement], config: SupplyNetworkElemenFeatureConfig = SupplyNetworkElemenFeatureConfig()) -> 'SupplyAggregatedNetworkElementLayer':
        super().__init__(SupplyAggregatedNetworkElementLayer._createLayerFromNetworkElements(networkElements, config), "Umlegung")

        self.networkElements = networkElements
        self.config = config

        renderer = self._createRenderer()
        self._qgsLayer.setRenderer(renderer)
        self._qgsLayer.triggerRepaint()

    @staticmethod
    def _createLayerFromNetworkElements(networkElements: List[AggregatedNetworkElement], config: SupplyNetworkElemenFeatureConfig) -> QgsVectorLayer:
        routeLayer = QgsVectorLayer("LineString?crs=EPSG:3857", 
                             SupplyAggregatedNetworkElementLayer.LayerName, "memory")
        pr = routeLayer.dataProvider()
        pr.addAttributes([
            QgsField(config.cfName, QVariant.String),
            QgsField(config.occupancyName , QVariant.Int),
            QgsField(config.occupancyNameCF2, QVariant.Int),
            QgsField(config.occupancyNameCF3, QVariant.Int),
            QgsField(config.occupancyNameCF4, QVariant.Int),
        ])
        routeLayer.updateFields()
        features = []
        for element in networkElements:
            features.append(element.toQgsFeature())
        pr.addFeatures(features)

        routeLayer.updateExtents()

        return routeLayer
    
    def _createRenderer(self) -> QgsCategorizedSymbolRenderer:
        renderer = QgsCategorizedSymbolRenderer(self.config.cfName)

        for cf in [ConnectivityFunction.VFS_2, ConnectivityFunction.VFS_3, ConnectivityFunction.VFS_4]:
            symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
            symbol.setColor(Style.getColorForCF(cf))
            symbol.setWidth(Style.getSizeForCF(cf))
            cat = QgsRendererCategory(cf.asStrShort(), symbol, cf.asStr())

            renderer.addCategory(cat)
        
        orderBy = QgsFeatureRequest.OrderBy([QgsFeatureRequest.OrderByClause(self.config.cfName, False)])
        renderer.setOrderByEnabled(True)
        renderer.setOrderBy(orderBy)
        
        return renderer

class BreakingPointsNetworkFeatureeConfig:
    def __init__(self, cfName: str = "Verbindungsfunktionsstufe", occupancyName: str = "Belegung") -> 'BreakingPointsNetworkFeatureeConfig':
        self.cfName = cfName
        self.occupancyName = occupancyName
        self.occupancyNameCF2 = "{} {}".format(occupancyName, ConnectivityFunction.VFS_2.asStrShort())
        self.occupancyNameCF3 = "{} {}".format(occupancyName, ConnectivityFunction.VFS_3.asStrShort())
        self.occupancyNameCF4 = "{} {}".format(occupancyName, ConnectivityFunction.VFS_4.asStrShort())

class BreakingPointsNetworkLayer(DigiRadLayer):
    LayerName = "Netzaufteilung"

    def __init__(self, breakingElements: List[BreakingElement], config: BreakingPointsNetworkFeatureeConfig = BreakingPointsNetworkFeatureeConfig()) -> 'BreakingPointsNetworkLayer':
        super().__init__(
            BreakingPointsNetworkLayer._createLayer(breakingElements, config),
            "Umlegung",
            expanded=False)

        self.breakingElements = breakingElements
        self.config = config

        renderer = self._createRenderer()
        self._qgsLayer.setRenderer(renderer)
        self._qgsLayer.triggerRepaint()

    @staticmethod
    def _createLayer(breakingElements: List[BreakingElement], config: BreakingPointsNetworkFeatureeConfig) -> QgsVectorLayer:
        layer = QgsVectorLayer("Point?crs=EPSG:3857", 
                             BreakingPointsNetworkLayer.LayerName, "memory")
        pr = layer.dataProvider()
        pr.addAttributes([
            QgsField(config.cfName, QVariant.String),
            QgsField(config.occupancyName , QVariant.Int),
            QgsField(config.occupancyNameCF2, QVariant.Int),
            QgsField(config.occupancyNameCF3, QVariant.Int),
            QgsField(config.occupancyNameCF4, QVariant.Int),
        ])
        layer.updateFields()
        features = []
        for breakingElement in breakingElements:
            features.append(breakingElement.toQgsFeature())
        pr.addFeatures(features)

        layer.updateExtents()

        return layer
    
    def _createRenderer(self) -> QgsCategorizedSymbolRenderer:
        renderer = QgsCategorizedSymbolRenderer(self.config.cfName)

        for cf in [ConnectivityFunction.VFS_2, ConnectivityFunction.VFS_3, ConnectivityFunction.VFS_4]:
            symbol = QgsMarkerSymbol.createSimple({'name': 'triangle'})
            symbol.setColor(Style.getColorForCF(cf))
            symbol.setSize(3.6)
            cat = QgsRendererCategory(cf.asStrShort(), symbol, cf.asStr())

            renderer.addCategory(cat)
        
        orderBy = QgsFeatureRequest.OrderBy([QgsFeatureRequest.OrderByClause(self.config.cfName, False)])
        renderer.setOrderByEnabled(True)
        renderer.setOrderBy(orderBy)
        
        return renderer