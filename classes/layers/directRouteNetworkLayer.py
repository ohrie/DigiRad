# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DirectRouteNetworklayer
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
    QgsLineSymbol,
    QgsFeatureRequest
    )

from .layer import DigiRadLayer
from ..network import ConnectivityFunction
from ..processing.directRouteNetwork import DirectRouteEntry
from ..styling import Style

class DirectRouteNetworkFeatureConfig:
    def __init__(self, cfName: str = "Verbindungsfunktionsstufe", relationName: str = "relation"):
        self.cfName = cfName
        self.relationName = relationName

class DirectRouteNetworklayer(DigiRadLayer):
    LayerName = "Luftliniennetz"

    def __init__(self, routeEntries: List[DirectRouteEntry], config: DirectRouteNetworkFeatureConfig = DirectRouteNetworkFeatureConfig()) -> Self:
        super().__init__(DirectRouteNetworklayer._createLayerFromRouteEntries(routeEntries, config))
        
        self.routeEntries = routeEntries
        self.config = config

        renderer = self._createRenderer(config.cfName)
        self._qgsLayer.setRenderer(renderer)
        self._qgsLayer.triggerRepaint()

    @staticmethod
    def _createLayerFromRouteEntries(routeEntries: DirectRouteEntry, config: DirectRouteNetworkFeatureConfig) -> Self:
        meshlayer = QgsVectorLayer("LineString?crs=EPSG:3857", DirectRouteNetworklayer.LayerName, "memory")
        pr = meshlayer.dataProvider()
        pr.addAttributes([QgsField(config.relationName, QVariant.LongLong),
                            QgsField(config.cfName,  QVariant.String)])
        meshlayer.updateFields() 

        feats = []
        for route in routeEntries:
            feat = QgsFeature()
            feat.setAttributes([route.relationId, route.cf.asStr()])
            feat.setGeometry(route.geometry())
            feats.append(feat)

        pr.addFeatures(feats)
        meshlayer.updateExtents()

        return meshlayer
        
    def _createRenderer(self, categoryField: str) -> QgsCategorizedSymbolRenderer:
        renderer = QgsCategorizedSymbolRenderer(categoryField)

        for cf in [ConnectivityFunction.VFS_2, ConnectivityFunction.VFS_3, ConnectivityFunction.VFS_4]:
            symbol = QgsLineSymbol.createSimple({'line_style':'dash'})
            symbol.setColor(Style.getColorForCF(cf))
            symbol.setWidth(Style.getSizeForCF(cf))
            cat = QgsRendererCategory(cf.asStr(), symbol, cf.asStr())

            renderer.addCategory(cat)
        
        orderBy = QgsFeatureRequest.OrderBy([QgsFeatureRequest.OrderByClause(self.config.cfName, False)])
        renderer.setOrderByEnabled(True)
        renderer.setOrderBy(orderBy)

        return renderer