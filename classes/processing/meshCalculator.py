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

from typing import List, Dict

from qgis.core import QgsPoint, QgsGeometry, QgsFeature, QgsPointXY, QgsVectorLayer, QgsCoordinateTransform
from qgis.analysis import QgsMeshTriangulation

from ...constants import CRS_STR
from ..helper import createPointHash, createDoublePointHash
from ..layers.centerLayerFeatures import CenterLayerFeature
from .directRouteEntry import DirectRouteEntry


class MeshCalculator:
    def __init__(self):
        pass

    def extractDirectRoutes(
            self, centerFeatures: List[CenterLayerFeature]) -> Dict[int, DirectRouteEntry]:
        routeEntries = {}
        # If only two features exist, the mesh calculation does not start, so
        # we have to handle it manually
        if len(centerFeatures) == 2:
            p1 = centerFeatures[0].geom
            p2 = centerFeatures[1].geom
            relationId = createDoublePointHash(p1, p2)
            routeEntries[relationId] = DirectRouteEntry(
                relationId, centerFeatures[0], centerFeatures[1])
        else:
            mesh = self._calculateMeshForFeatures(centerFeatures)
            pointIndex = self._createPointIndex(centerFeatures)

            for i in range(0, mesh.faceCount()):
                for entry in DirectRouteEntry.entriesFromMeshFace(
                        mesh, i, pointIndex):
                    if entry.relationId not in routeEntries:
                        routeEntries[entry.relationId] = entry

        return routeEntries

    def _createPointIndex(
            self, centerFeatures: List[CenterLayerFeature]) -> Dict[QgsPoint, CenterLayerFeature]:
        index = {}
        for feat in centerFeatures:
            index[createPointHash(feat.geom)] = feat

        return index

    def _calculateMeshForFeatures(
            self, centerFeatures: List[CenterLayerFeature]):
        # For PyQGIS 3.16: We do not have the .addVertex fn, so instead, we need to create a feature iterator and call
        # .addVertices

        features = []
        for feat in centerFeatures:
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromPointXY(
                QgsPointXY(feat.geom.x(), feat.geom.y())))
            features.append(feature)

        featureIterator = SimpleFeatureIterator(features)
        meshCalc = QgsMeshTriangulation()
        meshCalc.addVertices(
            featureIterator.getFeatures(), -1, QgsCoordinateTransform())

        mesh = meshCalc.triangulatedMesh()
        return mesh


class SimpleFeatureIterator:
    def __init__(self, features):
        layer = QgsVectorLayer(
            "Point?crs={}".format(CRS_STR),
            "temp_points",
            "memory"
        )
        provider = layer.dataProvider()
        provider.addFeatures(features)

        self.layer = layer

    def getFeatures(self):
        return self.layer.getFeatures()
