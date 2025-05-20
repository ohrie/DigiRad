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
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsMessageLog,
    QgsVectorLayer,
    QgsCategorizedSymbolRenderer,
    QgsMarkerSymbol,
    QgsRendererCategory,
    QgsField,
    QgsFeature,
    QgsSymbol,
    QgsWkbTypes)

from ..network import LevelOfCentrality
from ..processing.directRouteNetwork import DirectRouteEntry

class DirectRouteNetworkFeatureConfig:
    def __init__(self, locName: str = "loc", relationName: str = "relation"):
        self.locName = locName
        self.relationName = relationName

class DirectRouteNetworklayer:
    def __init__(self, routeEntries: List[DirectRouteEntry], config: DirectRouteNetworkFeatureConfig = DirectRouteNetworkFeatureConfig()) -> Self:
        layer = DirectRouteNetworklayer._createLayerFromRouteEntries(routeEntries, config)
        renderer = self._createRenderer(config.locName)
        layer.setRenderer(renderer)
        layer.triggerRepaint()

        self._layer = layer
        self.routeEntries = routeEntries
        self.config = config

        for routeEntry in self.routeEntries:
            QgsMessageLog.logMessage(f"{routeEntry.loc.asStr()}: {routeEntry.p1.x()} -> {routeEntry.p2.x()}")

    @staticmethod
    def _createLayerFromRouteEntries(routeEntries: DirectRouteEntry, config: DirectRouteNetworkFeatureConfig) -> Self:
        meshlayer = QgsVectorLayer("LineString?crs=EPSG:3857", "Luftliniennetz", "memory")
        pr = meshlayer.dataProvider()
        pr.addAttributes([QgsField(config.relationName, QVariant.LongLong),
                            QgsField(config.locName,  QVariant.String)])
        meshlayer.updateFields() 

        feats = []
        for route in routeEntries:
            feat = QgsFeature()
            feat.setAttributes([route.relationId, route.loc.asStr()])
            feat.setGeometry(route.geometry())
            feats.append(feat)

        pr.addFeatures(feats)
        meshlayer.updateExtents()

        return meshlayer
        
    def _createRenderer(self, categoryField: str) -> QgsCategorizedSymbolRenderer:
        renderer = QgsCategorizedSymbolRenderer(categoryField)

        categories = [
            [LevelOfCentrality.OBERZENTRUM.asStr(), QColor("red"), 0.7],
            [LevelOfCentrality.MITTELZENTRUM.asStr(), QColor("blue"), 0.5],
            [LevelOfCentrality.GRUNDZENTRUM.asStr(), QColor("green"), 0.2],
        ]

        for category in categories:
            symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
            symbol.setColor(category[1])
            symbol.setWidth(category[2])
            cat = QgsRendererCategory(category[0], symbol, category[0])

            renderer.addCategory(cat)
        
        return renderer
    

    def qgsLayer(self):
        return self._layer
    
    def name(self):
        return self._layer.name()