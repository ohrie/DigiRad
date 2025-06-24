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
    QgsLineSymbol)

from .layer import DigiRadLayer
from ..network import LevelOfCentrality, ConnectivityFunction
from ..processing.directRouteNetwork import DirectRouteEntry
from ..styling import Colors

class DirectRouteNetworkFeatureConfig:
    def __init__(self, cfName: str = "Verbindungsfunktionsstufe", relationName: str = "relation"):
        self.cfName = cfName
        self.relationName = relationName

class DirectRouteNetworklayer(DigiRadLayer):
    def __init__(self, routeEntries: List[DirectRouteEntry], config: DirectRouteNetworkFeatureConfig = DirectRouteNetworkFeatureConfig()) -> Self:
        super().__init__(DirectRouteNetworklayer._createLayerFromRouteEntries(routeEntries, config))
        renderer = self._createRenderer(config.cfName)
        self._qgsLayer.setRenderer(renderer)
        self._qgsLayer.triggerRepaint()

        self.routeEntries = routeEntries
        self.config = config

    @staticmethod
    def _createLayerFromRouteEntries(routeEntries: DirectRouteEntry, config: DirectRouteNetworkFeatureConfig) -> Self:
        meshlayer = QgsVectorLayer("LineString?crs=EPSG:3857", "Luftliniennetz", "memory")
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

        categories = [
            [ConnectivityFunction.VFS_2.asStr(), Colors.II, 0.7],
            [ConnectivityFunction.VFS_3.asStr(), Colors.III, 0.5],
            [ConnectivityFunction.VFS_4.asStr(), Colors.IV, 0.2],
        ]

        for category in categories:
            symbol = QgsLineSymbol.createSimple({'line_style':'dash'})
            symbol.setColor(category[1])
            symbol.setWidth(category[2])
            cat = QgsRendererCategory(category[0], symbol, category[0])

            renderer.addCategory(cat)
        
        return renderer