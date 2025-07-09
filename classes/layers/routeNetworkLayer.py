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
from typing import List

from PyQt5.QtCore import QVariant
from qgis.core import (
    QgsMessageLog,
    QgsVectorLayer,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsField,
    QgsFeature,
    QgsSymbol,
    QgsWkbTypes,
    QgsFeatureRequest
    )

from ...constants import CRS_STR
from .layer import DigiRadLayer
from ..network import ConnectivityFunction
from ..processing.routeNetwork import RouteEntry
from ..styling import Style

class RouteNetworkFeatureConfig:
    def __init__(self, cfName: str = "Verbindungsfunktionsstufe", relationName: str = "relation", detourName: str = "Umwegefaktor"):
        self.cfName = cfName
        self.relationName = relationName
        self.detourName = detourName

class RouteNetworklayer(DigiRadLayer):
    LayerName = "Umgelegte Relationen"

    def __init__(self, routeEntries: List[RouteEntry], layerName: str = "Umgelegte Relationen", groupName: str = "Umlegung", config: RouteNetworkFeatureConfig = RouteNetworkFeatureConfig()) -> 'RouteNetworklayer':
        super().__init__(
            RouteNetworklayer._createLayerFromRouteEntries(routeEntries, layerName, config),
            groupName,
            expanded=False,
            visible=False)
        
        self.routeEntries = routeEntries
        self.config = config
        
        renderer = self._createRenderer()
        self._qgsLayer.setRenderer(renderer)
        self._qgsLayer.triggerRepaint()
    
    def _createLayerFromRouteEntries(routeEntries: List[RouteEntry], layerName: str, config: RouteNetworkFeatureConfig) -> QgsVectorLayer:
        routeLayer = QgsVectorLayer("LineString?crs={}".format(CRS_STR), 
                            layerName, "memory")
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
    
    def _createRenderer(self) -> QgsCategorizedSymbolRenderer:
        renderer = QgsCategorizedSymbolRenderer(self.config.cfName)

        for cf in [ConnectivityFunction.VFS_2, ConnectivityFunction.VFS_3, ConnectivityFunction.VFS_4]:
            symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
            symbol.setColor(Style.getColorForCF(cf))
            symbol.setWidth(Style.getSizeForCF(cf))
            cat = QgsRendererCategory(cf.asStr(), symbol, cf.asStr())

            renderer.addCategory(cat)
        
        orderBy = QgsFeatureRequest.OrderBy([QgsFeatureRequest.OrderByClause(self.config.cfName, False)])
        renderer.setOrderByEnabled(True)
        renderer.setOrderBy(orderBy)
        
        return renderer
