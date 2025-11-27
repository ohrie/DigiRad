# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DirectRouteNetwork
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

import copy
from enum import Enum
from typing import List, Dict

from ..helper import createDoublePointHash
from qgis.core import QgsSpatialIndex, QgsPointXY

from ..network import LevelOfCentrality
from ..layers.centerLayer import CenterLayer
from ..layers.centerLayerFeatures import CenterLayerFeature
from .directRouteEntry import DirectRouteEntry
from .meshCalculator import MeshCalculator

class DirectRouteGenerateMethod(Enum):
    AUTO = 1
    MANUEL = 2
    LAYER = 3

    @staticmethod
    def default() -> 'DirectRouteGenerateMethod':
        return DirectRouteGenerateMethod.AUTO

class DirectRouteNetwork:
    def __init__(self, centerLayer: CenterLayer):
        self.centerLayer = centerLayer
    
    def createNetwork(self) -> List[DirectRouteEntry]:
        meshCalc = MeshCalculator()
        
        routesAll = meshCalc.extractDirectRoutes(self._getLocBasedFeatures([LevelOfCentrality.II, LevelOfCentrality.III, LevelOfCentrality.IV, LevelOfCentrality.Singular]))
        routesIII_II_S = meshCalc.extractDirectRoutes(self._getLocBasedFeatures([LevelOfCentrality.II, LevelOfCentrality.III, LevelOfCentrality.Singular, LevelOfCentrality.Surounding]))
        routesII = meshCalc.extractDirectRoutes(self._getLocBasedFeatures([LevelOfCentrality.II]))

        mergedRoutes = self._mergeCFRoutes(routesAll, routesIII_II_S)
        mergedRoutes = self._mergeCFRoutes(mergedRoutes, routesII)
        filteredRoutes = self._filterOutSuroundingToSuroundingRoutes(mergedRoutes)

        notConnectedSuroundings = self._connectNotConnectedSuroundings(filteredRoutes)

        return list(filteredRoutes.values()) + notConnectedSuroundings
    
    def _getLocBasedFeatures(self, locs: List[LevelOfCentrality]) -> List[CenterLayerFeature]:
        features = []
        for loc in locs:
            features += self.centerLayer.locFeatures[loc]
        
        return features
    
    def _mergeCFRoutes(self, routes1: Dict[int, DirectRouteEntry], routes2: Dict[int, DirectRouteEntry]) -> Dict[int, DirectRouteEntry]:
        merged = copy.copy(routes1)

        for routeId2 in routes2:
            if routeId2 in routes1:
                route1 = routes1[routeId2]
                route2 = routes2[routeId2]
                if route1.cf.isLowerEq(route2.cf):
                    merged[routeId2] = route2
            else:
                merged[routeId2] = routes2[routeId2]

        return merged
    
    def _filterOutSuroundingToSuroundingRoutes(self, routes: Dict[int, DirectRouteEntry]) -> Dict[int, DirectRouteEntry]:
        filtered = {}

        for (id, route) in routes.items():
            if route.feat1.loc == LevelOfCentrality.Surounding and route.feat2.loc == LevelOfCentrality.Surounding:
                continue
            filtered[id] = route
        
        return filtered
    
    def _connectNotConnectedSuroundings(self, routes: Dict[int, DirectRouteEntry]) -> List[DirectRouteEntry]:
        suroundingFeats = copy.copy(self.centerLayer.locFeatures[LevelOfCentrality.Surounding])
        
        # Remove all surounding features from the list which already are connected
        for route in routes.values():
            if route.feat1.loc == LevelOfCentrality.Surounding:
                if route.feat1 in suroundingFeats:
                    suroundingFeats.remove(route.feat1)
            if route.feat2.loc == LevelOfCentrality.Surounding:
                if route.feat2 in suroundingFeats:
                    suroundingFeats.remove(route.feat2)
        
        connectionCandidates = self._getLocBasedFeatures([LevelOfCentrality.II, LevelOfCentrality.III, LevelOfCentrality.Singular])

        index = QgsSpatialIndex()
        for (i, connectionCandiate) in enumerate(connectionCandidates):
            index.addFeature(i, connectionCandiate.geom.boundingBox())
        
        connectedRouteEntries = []
        for suroundingFeat in suroundingFeats:
            suroundingPoint = suroundingFeat.geom
            nearestFeatIds = index.nearestNeighbor(QgsPointXY(suroundingPoint.x(), suroundingPoint.y()), 1)
            if not nearestFeatIds:
                continue
            nearestFeat = connectionCandidates[nearestFeatIds[0]]
            relationId = createDoublePointHash(suroundingPoint, nearestFeat.geom)
            connectedRouteEntries.append(DirectRouteEntry(relationId, suroundingFeat, nearestFeat))
        
        return connectedRouteEntries

        
