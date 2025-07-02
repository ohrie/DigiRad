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

from qgis.core import QgsMessageLog, QgsPoint, QgsMesh, QgsGeometry, QgsFeature, QgsPointXY, QgsVectorLayer, QgsCoordinateTransform
from qgis.analysis import QgsMeshTriangulation

from ..helper import createPointHash, createDoublePointHash
from ..network import LevelOfCentrality, ConnectivityFunction
from ..layers.centerLayer import CenterLayer, CenterLayerFeature

class DirectRouteGenerateMethod(Enum):
    AUTO = 1
    MANUEL = 2

    @staticmethod
    def default() -> 'DirectRouteGenerateMethod':
        return DirectRouteGenerateMethod.AUTO

class DirectRouteEntry:
    def __init__(self, relationId: int, p1: QgsPoint, p2: QgsPoint, cf: ConnectivityFunction):
        self.relationId = relationId
        self.p1 = p1
        self.p2 = p2
        self.cf = cf
        self._geom = None
    
    @staticmethod
    def entryFromCenterFeatures(relationId: int, p1: QgsPoint, p2: QgsPoint, centerFeatureP1: CenterLayerFeature, centerFeatureP2: CenterLayerFeature) -> 'DirectRouteEntry':
        return DirectRouteEntry(relationId, p1, p2, LevelOfCentrality.getUpperLoc(centerFeatureP1.loc, centerFeatureP2.loc).toConnectivityFunction())
    
    @staticmethod
    def entriesFromMeshFace(mesh: QgsMesh, face: int, pointIndex: Dict[QgsPoint, CenterLayerFeature]) -> List['DirectRouteEntry']:
        (i1, i2, i3) = mesh.face(face)
        p1 = mesh.vertex(i1)
        p2 = mesh.vertex(i2)
        p3 = mesh.vertex(i3)

        featP1 = pointIndex[createPointHash(p1)]
        featP2 = pointIndex[createPointHash(p2)]
        featP3 = pointIndex[createPointHash(p3)]

        entries = []
        relationId = createDoublePointHash(p1, p2)

        entries.append(DirectRouteEntry.entryFromCenterFeatures(relationId, p1, p2, featP1, featP2))
        relationId = createDoublePointHash(p1, p3)
        entries.append(DirectRouteEntry.entryFromCenterFeatures(relationId, p1, p3, featP1, featP3))
        relationId = createDoublePointHash(p2, p3)
        entries.append(DirectRouteEntry.entryFromCenterFeatures(relationId, p2, p3, featP2, featP3))

        return entries
    
    def upgradeToMultipath(self, multiPath: QgsGeometry):
        self._geom = multiPath
    
    def geometry(self) -> QgsGeometry:
        if not self._geom:
            self._geom = QgsGeometry.fromPolyline([self.p1, self.p2])
        
        return self._geom
    
class DirectRouteNetwork:
    def __init__(self, centerLayer: CenterLayer):
        self.centerLayer = centerLayer
    
    def createNetwork(self) -> List[DirectRouteEntry]:
        meshCalc = MeshCalculator()
        
        routesAll = meshCalc.extractDirectRoutes(self._getLocBasedFeatures(list(LevelOfCentrality)))
        routesIII_II_S = meshCalc.extractDirectRoutes(self._getLocBasedFeatures([LevelOfCentrality.II, LevelOfCentrality.III, LevelOfCentrality.Singular]))
        routesII = meshCalc.extractDirectRoutes(self._getLocBasedFeatures([LevelOfCentrality.II]))

        mergedRoutes = self._mergeCFRoutes(routesAll, routesIII_II_S)
        mergedRoutes = self._mergeCFRoutes(mergedRoutes, routesII)

        return mergedRoutes.values()
    
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
        # For PyQGIS 3.16: We do not have the .addVertex fn, so instead, we need to create a feature iterator and call
        # .addVertices
        
        features = []
        for feat in centerFeatures:
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(feat.geom.x(), feat.geom.y())))
            features.append(feature)

        featureIterator = SimpleFeatureIterator(features)
        meshCalc = QgsMeshTriangulation()
        meshCalc.addVertices(featureIterator.getFeatures(), -1, QgsCoordinateTransform())
        
        mesh = meshCalc.triangulatedMesh()
        return mesh
    



class SimpleFeatureIterator:
    def __init__(self, features):
        layer = QgsVectorLayer(
            "Point?crs=EPSG:3857",
            "temp_points",
            "memory"
        )
        provider = layer.dataProvider()
        provider.addFeatures(features)

        self.layer = layer
    
    def getFeatures(self):
        return self.layer.getFeatures()