# -*- coding: utf-8 -*-
"""
/***************************************************************************
RouteNetwork
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

from typing import List, Tuple, Optional
from collections import OrderedDict

from qgis.core import (
    QgsMessageLog,
    QgsVectorLayer,
    QgsPoint,
    QgsPointXY,
    QgsGeometry,
)
from qgis.analysis import (
    QgsVectorLayerDirector,
    QgsNetworkStrategy,
    QgsNetworkDistanceStrategy,
    QgsGraphBuilder,
    QgsGraphAnalyzer,
)

from .networkValidator import Networkvalidator
from ..layers.directRouteNetworkLayer import DirectRouteNetworklayer, DirectRouteEntry
from .routing.cfRouting import GraphkModifier

class RouteGenerationOptions:
    def __init__(self, detourTolerance: float = 0.0, networkStrategy: QgsNetworkStrategy = QgsNetworkDistanceStrategy()):
        self.detourTolerance = detourTolerance
        self.networkStrategy = networkStrategy
    
    def detourToModifactionFactor(self) -> float:
        return 1.0 - self.detourTolerance
    
    def isDetourActive(self) -> bool:
        return self.detourTolerance != 0.0
    

class RouteEntry:
    def __init__(self, directRouteEntry: DirectRouteEntry, routeResult: 'RouteResult') -> 'RouteEntry':
        self.directRouteEntry = directRouteEntry
        self.routeResult = routeResult
        self.validation = Networkvalidator().validate(self)
    
    def geometry(self) -> QgsGeometry:
        return self.routeResult.geometry()
    
    def notFound(self) -> bool:
        return self.routeResult is None

class RouteNetwork:
    def __init__(self, networkLayer: QgsVectorLayer, directRouteLayer: DirectRouteNetworklayer):
        self.networkLayer = networkLayer
        self.directRouteLayer = directRouteLayer
    
    def createNetwork(self) -> List[RouteEntry]:
        pathFinder = NetworkPathFinder(self.networkLayer)
        # TODO: Batch processing for large numbers of route entries

        entries = list(self.directRouteLayer.routeEntries)[0:]

        QgsMessageLog.logMessage("Building graph..")
        pathFinder.buildGraph(entries)
        QgsMessageLog.logMessage("Done.")

        resultEntries = []
        QgsMessageLog.logMessage("Finding paths..")
        for routeEntry in entries:
            (pathPoints, cost) = pathFinder.findPathOfRelation(routeEntry.relationId)
            if not pathPoints:
                QgsMessageLog.logMessage(f"No path found for relation {routeEntry.relationId}")
            
            resultEntries.append(RouteEntry(routeEntry, pathPoints, cost))
        
        QgsMessageLog.logMessage("Done.")
        
        return resultEntries

class RouteResult:
    def __init__(self, edgeIds: List[int], points: List[QgsPoint], cost: float):
        self.edgeIds = edgeIds
        self.points = points
        self.cost = cost
        self._geom = None

    def geometry(self) -> QgsGeometry:
        if not self._geom:
            self._geom = QgsGeometry.fromPolyline(self.points)
        
        return self._geom

class NetworkPathFinder:
    """Class for finding multiple paths on a network without rebuilding the graph"""
    def __init__(self, networkLayer, options: RouteGenerationOptions, inclineField=None, direction=QgsVectorLayerDirector.Direction.DirectionBoth):
        """Initialize with a network layer and optional fields"""
        self.networkLayer = networkLayer
        self.options = options
        self.inclineField = inclineField
        self.direction = direction
        self.graph = None
        self.networkModifier = None
        self.director = None
        self._routeEntryIndex = None
        self.crs = networkLayer.crs()
        
        # Initialize the network topology
        self._buildDirector()
    
    def _buildDirector(self):
        """Set up the network director with appropriate strategy"""
        self.director = QgsVectorLayerDirector(
            self.networkLayer, -1, '', '', '', self.direction)
        
        self.director.addStrategy(self.options.networkStrategy)
        self.director.addStrategy(self.options.networkStrategy)
    
    def buildGraph(self, routeEntries: List[DirectRouteEntry]):
        """Build a graph including all the provided route entries"""
        self._routeEntryIndex = RouteEntryIndex(routeEntries)
        builder = QgsGraphBuilder(self.crs)
        self.tiedPoints = self.director.makeGraph(builder, self._routeEntryIndex.getTiedPoints())

        self.graph = builder.graph()
        self.graphModifier = GraphkModifier(self.graph, self.options.detourToModifactionFactor())
        
        return self.graph
    
    def findPathOfRelation(self, relationId: int, modifyGraph: bool = False) -> Optional[RouteResult]:
        """Find path of a relation"""
        indices = self._routeEntryIndex.getTiedIndicesOfRelation(relationId)
        if indices:
            # fromVertexIdx = self.tiedPoints[indices[0]]
            # toVertexIdx = self.tiedPoints[indices[1]]
            # return self.findPath(fromVertexIdx, toVertexIdx)
            return self.findPath(indices[0], indices[1], modifyGraph)
        else:
            return None
    
    def findPath(self, fromPointIdx, toPointIdx, modifyGraph: bool = False) -> Optional[RouteResult]:
        """Find path between two tied points by their index"""
        if not self.graph:
            raise ValueError("Graph has not been built. Call buildGraph first.")
            
        # Get vertex IDs from tied points
        fromVertex = self.graph.findVertex(self.tiedPoints[fromPointIdx])
        toVertex = self.graph.findVertex(self.tiedPoints[toPointIdx])
        
        # Calculate shortest path
        (tree, costs) = QgsGraphAnalyzer.dijkstra(self.graph, fromVertex, 1)
        
        if len(tree) == 0 or tree[toVertex] == -1:
            return None  # No path found
        
        # Add last point
        points = [self.graph.vertex(toVertex).point()]
        cost = costs[toVertex]
        edgeIds = []
        # Iterate the graph
        while fromVertex != toVertex:
            edgeId = tree[toVertex]
            toVertex = self.graph.edge(edgeId).fromVertex()
            points.append(self.graph.vertex(toVertex).point())
            edgeIds.append(edgeId)
        
        points.reverse()
        points = list(map(lambda p: QgsPoint(p.x(), p.y()), points))

        if modifyGraph:
            self.graphModifier.modifyEdgeCosts(edgeIds)

        return RouteResult(edgeIds, points, cost)
    
    def cleanUp(self):
        self.graphModifier.reset()

class RouteEntryIndexItem:
    def __init__(self, routeEntry: DirectRouteEntry, idxP1: int, idxP2: int):
        self.relationId = routeEntry.relationId
        self.p1 = routeEntry.p1
        self.p2 = routeEntry.p2
        self.cf = routeEntry.cf
        self.idxP1 = idxP1
        self.idxP2 = idxP2

class RouteEntryIndex:
    def __init__(self, routeEntries: List[DirectRouteEntry]):
        self._index = OrderedDict()
        for (i, entry) in enumerate(routeEntries):
            self._index[entry.relationId] = RouteEntryIndexItem(entry, i * 2, i * 2 + 1)
        

    def getTiedPoints(self) -> List[QgsPointXY]:
        tiedPoints = []
        for entry in self._index.values():
            tiedPoints.append(QgsPointXY(entry.p1.x(), entry.p1.y()))
            tiedPoints.append(QgsPointXY(entry.p2.x(), entry.p2.y()))
        
        return tiedPoints
    
    def getTiedIndicesOfRelation(self, relationId: int) -> Tuple[int, int]:
        if relationId in self._index:
            entry = self._index[relationId]
            return (entry.idxP1, entry.idxP2)
        else:
            return None