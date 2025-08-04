# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CenterLayerFeature
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
from qgis.core import (
    QgsMessageLog,
    QgsVectorLayer,
    QgsFeatureRequest,
    QgsPoint,
)

from ..network import LevelOfCentrality

class CenterLayerFeatureConfig:
    def __init__(self, locName: str = "Zentralität", nameName: str = "Bemerkung", arsName: str = "ARS"):
        self.locName = locName
        self.nameName = nameName
        self.arsName = arsName

class CenterLayerFeature:
    def __init__(self, featureId, name: str, loc: LevelOfCentrality, geom: QgsPoint) -> 'CenterLayerFeature':
        self.featureId = featureId
        self.name = name
        self.loc = loc
        self.geom = geom

    @staticmethod
    def featuresFromLayer(qgsLayer: QgsVectorLayer, config: CenterLayerFeatureConfig) -> Dict[LevelOfCentrality, List['CenterLayerFeature']]:
        features = {}
        for loc in LevelOfCentrality:
            features[loc] = []
        
        nameIdx = qgsLayer.fields().indexFromName(config.nameName)
        locIdx = qgsLayer.fields().indexFromName(config.locName)
        request = QgsFeatureRequest()
        request.setSubsetOfAttributes([locIdx, nameIdx])
        for feat in qgsLayer.getFeatures(request):
            name = feat.attributes()[nameIdx]
            loc = feat.attributes()[locIdx]
            try:
                loc = LevelOfCentrality.fromStr(loc)
            except Exception as e:
                QgsMessageLog.logMessage(f"Unable to get level of centrality for feature {feat.id()} ({name}): {e}")
                continue
            geom = feat.geometry()
            if not geom:
                continue
            geom = geom.asPoint()
            geom = QgsPoint(geom.x(), geom.y())
            features[loc].append(CenterLayerFeature(feat.id(), name, loc, geom))

        return features
