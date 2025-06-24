# -*- coding: utf-8 -*-
"""
/***************************************************************************
RouteNetworklayer
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

from PyQt5.QtCore import QVariant
from qgis.core import (
    QgsMessageLog,
    QgsVectorLayer,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsField,
    QgsFeature,
    QgsSymbol,
    QgsWkbTypes)

from .layer import DigiRadLayer
from ..network import ConnectivityFunction
from ..processing.directRouteNetwork import DirectRouteEntry
from ..processing.routeNetwork import RouteEntry
from ..styling import Colors

class RouteNetworkFeatureConfig:
    def __init__(self, cfName: str = "Verbindungsfunktionsstufe", relationName: str = "relation", detourName: str = "Umwegefaktor"):
        self.cfName = cfName
        self.relationName = relationName
        self.detourName = detourName

class RouteNetworklayer(DigiRadLayer):
    def __init__(self, routeEntries: List[DirectRouteEntry], config: RouteNetworkFeatureConfig = RouteNetworkFeatureConfig()) -> Self:
        super().__init__(RouteNetworklayer._createLayerFromRouteEntries(routeEntries, config))
        renderer = self._createRenderer(config.cfName)
        self._qgsLayer.setRenderer(renderer)
        self._qgsLayer.triggerRepaint()

        self.routeEntries = routeEntries
        self.config = config
    
    def _createLayerFromRouteEntries(routeEntries: List[RouteEntry], config: RouteNetworkFeatureConfig) -> QgsVectorLayer:
        routeLayer = QgsVectorLayer("LineString?crs=EPSG:3857", 
                             "Umgelegtes Netz", "memory")
        pr = routeLayer.dataProvider()
        pr.addAttributes([
            QgsField(config.relationName, QVariant.LongLong),
            QgsField(config.cfName, QVariant.String),
            QgsField(config.detourName, QVariant.Double),
            QgsField("cost", QVariant.Double)
        ])
        routeLayer.updateFields()

        feats = []
        for route in routeEntries:
            if route.notFound():
                QgsMessageLog.logMessage(f"Route not found {route.directRouteEntry.relationId}")
                continue
            feat = QgsFeature()
            feat.setAttributes([route.directRouteEntry.relationId, route.directRouteEntry.cf.asStr(), route.validation.detourFactor, route.routeResult.cost])
            feat.setGeometry(route.geometry())
            feats.append(feat)

        pr.addFeatures(feats)

        routeLayer.updateExtents()

        return routeLayer
    
    def _createRenderer(self, categoryField: str) -> QgsCategorizedSymbolRenderer:
        renderer = QgsCategorizedSymbolRenderer(categoryField)

        categories = [
            [ConnectivityFunction.VFS_2.asStr(), Colors.II, 0.7],
            [ConnectivityFunction.VFS_3.asStr(), Colors.III, 0.5],
            [ConnectivityFunction.VFS_4.asStr(), Colors.IV, 0.4],
        ]

        for category in categories:
            symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
            symbol.setColor(category[1])
            symbol.setWidth(category[2])
            cat = QgsRendererCategory(category[0], symbol, category[0])

            renderer.addCategory(cat)
        
        return renderer
