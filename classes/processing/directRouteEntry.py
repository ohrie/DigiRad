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

from qgis.core import QgsPoint, QgsMesh, QgsGeometry

from ..helper import createPointHash, createDoublePointHash
from ..network import LevelOfCentrality, ConnectivityFunction
from ..layers.centerLayerFeatures import CenterLayerFeature


class DirectRouteEntry:
    def __init__(self, relationId: int, feat1: CenterLayerFeature,
                 feat2: CenterLayerFeature):
        self.relationId = relationId
        self.feat1 = feat1
        self.feat2 = feat2
        self.cf = DirectRouteEntry._getConnectivityFunction(feat1, feat2)
        self._geom = None

    @staticmethod
    def _getConnectivityFunction(
            feat1: CenterLayerFeature, feat2: CenterLayerFeature) -> ConnectivityFunction:
        # Special case: one LoC is Z II, the other is surrounding but of type Z
        # II
        z2Count = 0
        for f in [feat1, feat2]:
            if f.loc == LevelOfCentrality.Surrounding:
                if f.ars.isZ2():
                    z2Count += 1
            elif f.loc == LevelOfCentrality.II:
                z2Count += 1

        if z2Count == 2:
            return ConnectivityFunction.VFS_2
        else:
            return LevelOfCentrality.getUpperLoc(
                feat1.loc, feat2.loc).toConnectivityFunction()

    @staticmethod
    def entriesFromMeshFace(mesh: QgsMesh, face: int,
                            pointIndex: Dict[QgsPoint, CenterLayerFeature]) -> List['DirectRouteEntry']:
        (i1, i2, i3) = mesh.face(face)
        p1 = mesh.vertex(i1)
        p2 = mesh.vertex(i2)
        p3 = mesh.vertex(i3)

        featP1 = pointIndex[createPointHash(p1)]
        featP2 = pointIndex[createPointHash(p2)]
        featP3 = pointIndex[createPointHash(p3)]

        entries = []
        relationId = createDoublePointHash(p1, p2)

        entries.append(DirectRouteEntry(relationId, featP1, featP2))
        relationId = createDoublePointHash(p1, p3)
        entries.append(DirectRouteEntry(relationId, featP1, featP3))
        relationId = createDoublePointHash(p2, p3)
        entries.append(DirectRouteEntry(relationId, featP2, featP3))

        return entries

    def upgradeToMultipath(self, multiPath: QgsGeometry):
        self._geom = multiPath

    def geometry(self) -> QgsGeometry:
        if not self._geom:
            self._geom = QgsGeometry.fromPolyline([self.p1(), self.p2()])

        return self._geom

    def p1(self) -> QgsPoint:
        return self.feat1.geom

    def p2(self) -> QgsPoint:
        return self.feat2.geom
