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
from typing import List, Dict, Self

from qgis.core import QgsMessageLog, QgsPoint, QgsMesh, QgsGeometry
from qgis.analysis import QgsMeshTriangulation

from ..helper import createPointHash, createDoublePointHash
from ..network import LevelOfCentrality
from ..layers.centerLayer import CenterLayer, CenterLayerFeature

class DirectRouteEntry:
    def __init__(self, relationId: int, p1: QgsPoint, p2: QgsPoint, centerFeatureP1: CenterLayerFeature, centerFeatureP2: CenterLayerFeature):
        self.relationId = relationId
        self.p1 = p1
        self.p2 = p2
        self.loc = LevelOfCentrality.getUpperLoc(centerFeatureP1.loc, centerFeatureP2.loc)
        self._geom = None
    
    @staticmethod
    def entriesFromMeshFace(mesh: QgsMesh, face: int, pointIndex: Dict[QgsPoint, CenterLayerFeature]) -> List[Self]:
        (i1, i2, i3) = mesh.face(face)
        p1 = mesh.vertex(i1)
        p2 = mesh.vertex(i2)
        p3 = mesh.vertex(i3)

        featP1 = pointIndex[createPointHash(p1)]
        featP2 = pointIndex[createPointHash(p2)]
        featP3 = pointIndex[createPointHash(p3)]

        entries = []
        relationId = createDoublePointHash(p1, p2)
        entries.append(DirectRouteEntry(relationId, p1, p2, featP1, featP2))
        relationId = createDoublePointHash(p1, p3)
        entries.append(DirectRouteEntry(relationId, p1, p3, featP1, featP3))
        relationId = createDoublePointHash(p2, p3)
        entries.append(DirectRouteEntry(relationId, p2, p3, featP2, featP3))

        return entries
    
    def geometry(self) -> QgsGeometry:
        if not self._geom:
            self._geom = QgsGeometry.fromPolyline([self.p1, self.p2])
        
        return self._geom

class DirectRouteNetwork:
    def __init__(self, centerLayer: CenterLayer):
        self.centerLayer = centerLayer
    
    def createNetwork(self):
        meshCalc = MeshCalculator()
        routesAll = meshCalc.extractDirectRoutes(
            self.centerLayer.locFeatures[LevelOfCentrality.GRUNDZENTRUM] + 
            self.centerLayer.locFeatures[LevelOfCentrality.MITTELZENTRUM] +
            self.centerLayer.locFeatures[LevelOfCentrality.OBERZENTRUM])
        routesMZ_OZ = meshCalc.extractDirectRoutes(
            self.centerLayer.locFeatures[LevelOfCentrality.MITTELZENTRUM] +
            self.centerLayer.locFeatures[LevelOfCentrality.OBERZENTRUM])
        routesOZ = meshCalc.extractDirectRoutes(self.centerLayer.locFeatures[LevelOfCentrality.OBERZENTRUM])

        mergedRoutes = self._mergeLocRoutes(routesAll, routesMZ_OZ)
        mergedRoutes = self._mergeLocRoutes(mergedRoutes, routesOZ)

        return mergedRoutes.values()
    
    def _mergeLocRoutes(self, routes1: Dict[int, DirectRouteEntry], routes2: Dict[int, DirectRouteEntry]) -> Dict[int, DirectRouteEntry]:
        merged = copy.copy(routes1)

        for routeId2 in routes2:
            if routeId2 in routes1:
                route1 = routes1[routeId2]
                route2 = routes2[routeId2]
                if route1.loc.isLowerEq(route2.loc):
                    merged[routeId2] = route2
            else:
                merged[routeId2] = routes2[routeId2]

        return merged
        
class MeshCalculator:
    def __init__(self):
        pass
    
    def extractDirectRoutes(self, centerFeatures: List[CenterLayerFeature]) -> Dict[int, DirectRouteEntry]:
        mesh = self._calculateMeshForFeatures(centerFeatures)
        pointIndex = self._createPointIndex(centerFeatures)

        routeEntries = {}
        for i in range(0, mesh.faceCount()):
            for entry in DirectRouteEntry.entriesFromMeshFace(mesh, i, pointIndex):
                if not entry.relationId in routeEntries:
                    routeEntries[entry.relationId] = entry
        
        return routeEntries
    
    def _createPointIndex(self, centerFeatures: List[CenterLayerFeature]) -> Dict[QgsPoint, CenterLayerFeature]:
        index = {}
        for feat in centerFeatures:
            index[createPointHash(feat.geom)] = feat
        
        return index

    def _calculateMeshForFeatures(self, centerFeatures: List[CenterLayerFeature]):
        meshCalc = QgsMeshTriangulation()
        for feat in centerFeatures:
            meshCalc.addVertex(feat.geom)
        
        mesh = meshCalc.triangulatedMesh()
        return mesh