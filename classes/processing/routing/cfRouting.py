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

from typing import List, Tuple
from copy import deepcopy

from qgis.core import QgsMessageLog
from qgis.analysis import QgsGraph

from ...helper import createDoublePointHash

class GraphkModifier:
    def __init__(self, graph: QgsGraph, modificationFactor: int):
        self.graph = graph
        self.modificationFactor = modificationFactor
        self._oldEdges = set()
        self._modifiedEdges = set()
        self.changeLog = dict()
    
    def modifyEdgeCostsBasedOnChangelog(self, minBound: float = 0.55, multiplier: float = 0.02):
        changelog = deepcopy(self.changeLog)

        fwRevEdgeIdMap = self._createFwRevEdgeIdMap()

        countSortedChangelog = dict()
        for (edgeId1, edgeId2, count) in fwRevEdgeIdMap.values():
            if count == 1:
                continue
            
            if count in countSortedChangelog:
                countSortedChangelog[count].append(edgeId1)
                countSortedChangelog[count].append(edgeId2)
            else:
                countSortedChangelog[count] = [edgeId1, edgeId2]
        
        for (count, edgeIds) in countSortedChangelog.items():
            modificationFactor = max(minBound, self.modificationFactor - (count * multiplier))
            self._modifyEdgeCostInner(edgeIds, modificationFactor)
        
        self.changeLog = changelog
    
    def _createFwRevEdgeIdMap(self):
        fwRevEdgeIdMap = {}
        for (edgeId, count) in self.changeLog.items():
            oppositeEdge = self._findOppositeEdgeId(edgeId)
            edge = self.graph.edge(edgeId)
            v1 = self.graph.vertex(edge.fromVertex()).point()
            v2 = self.graph.vertex(edge.toVertex()).point()
            edgeKey = createDoublePointHash(v1, v2)
            if edgeKey in fwRevEdgeIdMap:
                n = fwRevEdgeIdMap[edgeKey][2] + count
            else:
                n = count
            fwRevEdgeIdMap[edgeKey] = (edgeId, oppositeEdge, n)
        
        return fwRevEdgeIdMap


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


            revEdgeId = self._findOppositeEdgeId(edgeId)
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
    
    def _findOppositeEdgeId(self, edgeId: int) -> int:
        # Get the edge at the given index
        edge = self.graph.edge(edgeId)
        
        # Get the from and to vertices of this edge
        from_vertex = edge.fromVertex()
        to_vertex = edge.toVertex()
        
        # Get the vertex at the 'to' position
        if to_vertex < 0 or to_vertex >= self.graph.vertexCount():
            return -1
            
        vertex = self.graph.vertex(to_vertex)
        
        # Get outgoing edges from the 'to' vertex
        outgoing_edges = vertex.outgoingEdges()
        
        # Look for edges which start at toVertex and end at fromVertex
        for candidate_index in outgoing_edges:
            if candidate_index < 0 or candidate_index >= self.graph.edgeCount():
                continue
                
            candidate_edge = self.graph.edge(candidate_index)
            
            # Check if this candidate edge goes back to the original fromVertex
            if candidate_edge.toVertex() == from_vertex:
                return candidate_index
        
        # No opposite edge found
        return -1
    
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
                
