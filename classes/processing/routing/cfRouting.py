# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CFRouting
                                 A QGIS plugin
 Unterstützung bei der Erstellung von digitalen Angebotsnetzen für den Radverkehr
                             -------------------
        begin                : 2025-05-13
        copyright            : (C) 2025 by Vision Velo UG (haftungsbeschränkt)
        email                : info@vision-velo.de
        git sha              : $Format:%H$
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

from typing import List, Tuple
from copy import deepcopy

from qgis.core import QgsMessageLog
from qgis.analysis import (
    QgsGraph,
)

class GraphkModifier:
    def __init__(self, graph: QgsGraph, modificationFactor: int):
        self.graph = graph
        self.modificationFactor = modificationFactor
        self._oldEdges = set()
        self._modifiedEdges = set()
        self.changeLog = dict()
    
    def modifyEdgeCostsBasedOnChangelog(self, minBound: float = 0.5, multiplier: float = 0.05):
        changelog = deepcopy(self.changeLog)

        countSortedChangelog = dict()
        for (edgeId, count) in changelog.items():
            if count == 1:
                continue
            
            if count in countSortedChangelog:
                countSortedChangelog[count].append(edgeId)
            else:
                countSortedChangelog[count] = [edgeId]
        
        for (count, edgeIds) in countSortedChangelog.items():
            modificationFactor = max(minBound, self.modificationFactor - (count * multiplier))
            QgsMessageLog.logMessage(f"For count {count} {len(edgeIds)} items and modfactor {modificationFactor}")
            self._modifyEdgeCostInner(edgeIds, modificationFactor)
        
        self.changeLog = changelog

    def modifyEdgeCosts(self, edgeIds: List[int]):
        if self.modificationFactor == 1:
            return
        
        (newEdgeIds, oldEdgeIds) = self._modifyEdgeCostInner(edgeIds, self.modificationFactor)
        self._modifiedEdges.update(newEdgeIds)
        self._oldEdges.update(oldEdgeIds)
    
    def _modifyEdgeCostInner(self, edgeIds: List[int], factor: float) -> Tuple[List[int], List[int]]:
        newEdgeIds = set()
        oldEdgeIds = set()
        for edgeId in edgeIds:
            edge = self.graph.edge(edgeId)
            baseCost = edge.cost(0)

            newEdgeId = self.graph.addEdge(
                edge.fromVertex(),
                edge.toVertex(),
                [baseCost, baseCost * factor]
            )

            self._updateChangeLog(edgeId, newEdgeId)
            newEdgeIds.add(newEdgeId)
            oldEdgeIds.add(edgeId)


            revEdgeId = self.graph.findOppositeEdge(edgeId)
            revEdge = self.graph.edge(revEdgeId)
            baseCost = revEdge.cost(0)
            newRevEdgeId = self.graph.addEdge(
                revEdge.fromVertex(),
                revEdge.toVertex(),
                [baseCost, baseCost * factor]
            )

            self._updateChangeLog(revEdgeId, newRevEdgeId)
            newEdgeIds.add(newRevEdgeId)
            oldEdgeIds.add(revEdgeId)
            
        return (newEdgeIds, oldEdgeIds)
    
    def _updateChangeLog(self, oldEdgeId, newEdgeId):
        if oldEdgeId in self.changeLog:
            count = self.changeLog[oldEdgeId]
            del self.changeLog[oldEdgeId]
            self.changeLog[newEdgeId] = count + 1
        else:
            self.changeLog[newEdgeId] = 1
    
    def removeOldEdges(self):
        for edgeId in self._oldEdges:
            if self.graph.hasEdge(edgeId):
                self.graph.removeEdge(edgeId)
        
        self._oldEdges.clear()
    
    def reset(self):
        filteredEdgeIds = []
        for edgeId in self._modifiedEdges:
            if self.graph.hasEdge(edgeId):
                filteredEdgeIds.append(edgeId)
        
        (newEdgeIds, oldEdgeIds) = self._modifyEdgeCostInner(filteredEdgeIds, 1)
        self._modifiedEdges.clear()
        self._oldEdges.update(oldEdgeIds)

        self.removeOldEdges()
        self.changeLog.clear()
                
