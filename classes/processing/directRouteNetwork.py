# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 Vision Velo GmbH

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
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
        routesIII_II_S = meshCalc.extractDirectRoutes(self._getLocBasedFeatures([LevelOfCentrality.II, LevelOfCentrality.III, LevelOfCentrality.Singular, LevelOfCentrality.Surrounding]))
        routesII = meshCalc.extractDirectRoutes(self._getLocBasedFeatures([LevelOfCentrality.II]))

        mergedRoutes = self._mergeCFRoutes(routesAll, routesIII_II_S)
        mergedRoutes = self._mergeCFRoutes(mergedRoutes, routesII)
        filteredRoutes = self._filterOutSurroundingToSurroundingRoutes(mergedRoutes)

        notConnectedSurroundings = self._connectNotConnectedSurroundings(filteredRoutes)

        return list(filteredRoutes.values()) + notConnectedSurroundings
    
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
    
    def _filterOutSurroundingToSurroundingRoutes(self, routes: Dict[int, DirectRouteEntry]) -> Dict[int, DirectRouteEntry]:
        filtered = {}

        for (id, route) in routes.items():
            if route.feat1.loc == LevelOfCentrality.Surrounding and route.feat2.loc == LevelOfCentrality.Surrounding:
                continue
            filtered[id] = route
        
        return filtered
    
    def _connectNotConnectedSurroundings(self, routes: Dict[int, DirectRouteEntry]) -> List[DirectRouteEntry]:
        surroundingFeats = copy.copy(self.centerLayer.locFeatures[LevelOfCentrality.Surrounding])
        
        # Remove all surrounding features from the list which already are connected
        for route in routes.values():
            if route.feat1.loc == LevelOfCentrality.Surrounding:
                if route.feat1 in surroundingFeats:
                    surroundingFeats.remove(route.feat1)
            if route.feat2.loc == LevelOfCentrality.Surrounding:
                if route.feat2 in surroundingFeats:
                    surroundingFeats.remove(route.feat2)
        
        connectionCandidates = self._getLocBasedFeatures([LevelOfCentrality.II, LevelOfCentrality.III, LevelOfCentrality.Singular])

        index = QgsSpatialIndex()
        for (i, connectionCandiate) in enumerate(connectionCandidates):
            index.addFeature(i, connectionCandiate.geom.boundingBox())
        
        connectedRouteEntries = []
        for surroundingFeat in surroundingFeats:
            surroundingPoint = surroundingFeat.geom
            nearestFeatIds = index.nearestNeighbor(QgsPointXY(surroundingPoint.x(), surroundingPoint.y()), 1)
            if not nearestFeatIds:
                continue
            nearestFeat = connectionCandidates[nearestFeatIds[0]]
            relationId = createDoublePointHash(surroundingPoint, nearestFeat.geom)
            connectedRouteEntries.append(DirectRouteEntry(relationId, surroundingFeat, nearestFeat))
        
        return connectedRouteEntries

        
