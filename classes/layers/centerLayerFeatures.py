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
from qgis.core import (
    QgsMessageLog,
    QgsVectorLayer,
    QgsPoint,
)

from ..network import LevelOfCentrality
from ..ars import ARSCodeStr

class CenterLayerFeatureConfig:
    def __init__(self, locName: str = "Zentralitaet", nameName: str = "Bemerkung", arsName: str = "ARS"):
        self.locName = locName
        self.nameName = nameName
        self.arsName = arsName

class CenterLayerFeature:
    def __init__(self, featureId, name: str, ars: ARSCodeStr, loc: LevelOfCentrality, geom: QgsPoint) -> 'CenterLayerFeature':
        self.featureId = featureId
        self.name = name
        self.ars = ars
        self.loc = loc
        self.geom = geom

    @staticmethod
    def featuresFromLayer(qgsLayer: QgsVectorLayer, config: CenterLayerFeatureConfig) -> Dict[LevelOfCentrality, List['CenterLayerFeature']]:
        features = {}
        for loc in LevelOfCentrality:
            features[loc] = []
        
        nameIdx = qgsLayer.fields().indexFromName(config.nameName)
        arsIdx = qgsLayer.fields().indexFromName(config.arsName)
        locIdx = qgsLayer.fields().indexFromName(config.locName)
        for feat in qgsLayer.getFeatures():
            name = feat.attributes()[nameIdx]
            arsStr = str(feat.attributes()[arsIdx])
            loc = feat.attributes()[locIdx]
            try:
                loc = LevelOfCentrality.fromStr(loc)
            except Exception as e:
                QgsMessageLog.logMessage(f"Unable to get level of centrality for feature {feat.id()} ({name}): {e}")
                continue
            geom = feat.geometry()
            if not geom:
                continue
            if geom.isMultipart():
                if not geom.convertToSingleType():
                    QgsMessageLog.logMessage("Unable to convert to single")
                    continue
            
            ars = ARSCodeStr.fromStr(arsStr)
            if not ars:
                QgsMessageLog.logMessage(f"Unable to create ars code from {arsStr}")
                ars = ARSCodeStr.empty()
            
            geom = geom.asPoint()
            geom = QgsPoint(geom.x(), geom.y())
            features[loc].append(CenterLayerFeature(feat.id(), name, ars, loc, geom))

        return features
