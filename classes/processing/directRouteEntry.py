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

from typing import List, Dict

from qgis.core import QgsMessageLog, QgsPoint, QgsMesh, QgsGeometry

from ..helper import createPointHash, createDoublePointHash
from ..network import LevelOfCentrality
from ..layers.centerLayerFeatures import CenterLayerFeature

class DirectRouteEntry:
    def __init__(self, relationId: int, feat1: CenterLayerFeature, feat2: CenterLayerFeature):
        self.relationId = relationId
        self.feat1 = feat1
        self.feat2 = feat2
        self.cf = LevelOfCentrality.getUpperLoc(feat1.loc, feat2.loc).toConnectivityFunction()
        self._geom = None
    
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
