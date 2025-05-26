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

from typing import Self, List, Tuple
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
    QgsNetworkDistanceStrategy,
    QgsGraphBuilder,
    QgsGraphAnalyzer,
)

from .networkValidator import Networkvalidator
from ..layers.directRouteNetworkLayer import DirectRouteNetworklayer, DirectRouteEntry

class RouteEntry:
    def __init__(self, directRouteEntry: DirectRouteEntry, pathPoints: List[QgsPoint], cost: int = -1) -> Self:
        self.directRouteEntry = directRouteEntry
        self.pathPoints = pathPoints
        self.cost = cost
        self._geom = None
        self.validation = Networkvalidator().validate(self)
    
    def geometry(self) -> QgsGeometry:
        if not self._geom and not self.notFound():
            self._geom = QgsGeometry.fromPolyline(self.pathPoints)
        
        return self._geom
    
    def notFound(self) -> bool:
        return self.pathPoints is None

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

class NetworkPathFinder:
    """Class for finding multiple paths on a network without rebuilding the graph"""
    def __init__(self, networkLayer, inclineField=None, direction=QgsVectorLayerDirector.Direction.DirectionBoth):
        """Initialize with a network layer and optional fields"""
        self.networkLayer = networkLayer
        self.inclineField = inclineField
        self.direction = direction
        self.graph = None
        self.director = None
        self._routeEntryIndex = None
        self.crs = networkLayer.crs()
        
        # Initialize the network topology
        self._buildDirector()
    
    def _buildDirector(self):
        """Set up the network director with appropriate strategy"""
        self.director = QgsVectorLayerDirector(
            self.networkLayer, -1, '', '', '', self.direction)
        
        # Add strategy based on available fields
        if (self.inclineField and 
                self.inclineField in [field.name() for field in self.networkLayer.fields()]):
            inclineIdx = self.networkLayer.fields().indexFromName(self.inclineField)
            
            # TODO: Update to use incline instead
            class InclineStrategy(QgsNetworkDistanceStrategy):
                def cost(self, distance, feature):
                    incline = feature.attributes()[inclineIdx]
                    if not incline:
                        incline = 1  # Default incline
                    # Time in seconds
                    # TODO: Create a proper incline cost function 
                    return distance * incline
                    
            self.director.addStrategy(InclineStrategy())
        else:
            self.director.addStrategy(QgsNetworkDistanceStrategy())
    
    def buildGraph(self, routeEntries: List[DirectRouteEntry]):
        """Build a graph including all the provided route entries"""
        self._routeEntryIndex = RouteEntryIndex(routeEntries)
        builder = QgsGraphBuilder(self.crs)
        self.tiedPoints = self.director.makeGraph(builder, self._routeEntryIndex.getTiedPoints())

        self.graph = builder.graph()
        return self.graph
    
    def findPathOfRelation(self, relationId: int):
        """Find path of a relation"""
        indices = self._routeEntryIndex.getTiedIndicesOfRelation(relationId)
        if indices:
            # fromVertexIdx = self.tiedPoints[indices[0]]
            # toVertexIdx = self.tiedPoints[indices[1]]
            # return self.findPath(fromVertexIdx, toVertexIdx)
            return self.findPath(indices[0], indices[1])
        else:
            return None
    
    def findPath(self, fromPointIdx, toPointIdx):
        """Find path between two tied points by their index"""
        if not self.graph:
            raise ValueError("Graph has not been built. Call buildGraph first.")
            
        # Get vertex IDs from tied points
        fromVertex = self.graph.findVertex(self.tiedPoints[fromPointIdx])
        toVertex = self.graph.findVertex(self.tiedPoints[toPointIdx])
        
        print(fromPointIdx, fromVertex)
        print(toPointIdx, toVertex)
        
        # Calculate shortest path
        (tree, cost) = QgsGraphAnalyzer.dijkstra(self.graph, fromVertex, 0)
        
        # print(len(tree))
        
        if len(tree) == 0 or tree[toVertex] == -1:
            return None, None  # No path found
        
        # Add last point
        route = [self.graph.vertex(toVertex).point()]
        # Iterate the graph
        while fromVertex != toVertex:
            toVertex = self.graph.edge(tree[toVertex]).fromVertex()
            route.append(self.graph.vertex(toVertex).point())
        route.reverse()
        route = list(map(lambda p: QgsPoint(p.x(), p.y()), route))
        
        return route, cost[toVertex]

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