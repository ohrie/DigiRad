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

from qgis.core import (
    QgsMessageLog,
    QgsVectorLayer,
    QgsFeature
)
from qgis.analysis import (
    QgsNetworkDistanceStrategy,
)

class NetworkDemandProperties:
    def __init__(self, demandFieldIdx: int, dMax: int, p80: float):
        self.demandFieldIdx = demandFieldIdx
        self.dMax = dMax
        self.p80 = p80

    @staticmethod
    def fromLayer(networkLayer: QgsVectorLayer, demandFieldName: str) -> 'NetworkDemandProperties':
        fields = networkLayer.fields()
        demandFieldIdx = fields.indexFromName(demandFieldName)
        if demandFieldIdx == -1:
            raise Exception(f"{demandFieldName} could not be found in layer {networkLayer.name()}")
        
        # Calculate percentiles
        # demands = []
        dMax = 0
        for feat in networkLayer.getFeatures():
            demand = feat[demandFieldIdx]
            if demand > dMax:
                dMax = demand
            # if demand and demand > 0:
            #     demands.append(demand)
        
        # if demands:
        #     demands.sort()
        #     dMax = demands[-1]
        #     demands = np.array(demands)
        #     p80 = np.percentile(demands, 80)
        # else:
        #     dMax = 0
        #     p80 = 0
        
        return NetworkDemandProperties(demandFieldIdx, dMax, 0)


class DemandNetworkStrategy(QgsNetworkDistanceStrategy):
    def __init__(self, demandNetworkProperties: NetworkDemandProperties):
        super().__init__()
        self.demandNetworkProperties = demandNetworkProperties
    
    def cost(self, distance: float, f: QgsFeature):
        demand = f.attributes()[self.demandNetworkProperties.demandFieldIdx]
        if demand:
            demand = int(demand)
            if demand > 0 and self.demandNetworkProperties.dMax > 0:
                excessDemand = demand / self.demandNetworkProperties.dMax
                # Maximal 50% reduction
                reductionFactor = 1.0 - (0.5 * excessDemand)
                cost = distance * reductionFactor
                return cost
        
        # No demand or invalid demand value - return full distance
        return distance
    
    def requiredAttributes(self):
        return [self.demandNetworkProperties.demandFieldIdx]