# -*- coding: utf-8 -*-
"""
/***************************************************************************
RouteNetworkAnalyser
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

from typing import List, Set, Dict, Tuple, Optional
from collections import defaultdict, deque

from qgis.core import (
    QgsMessageLog,
    QgsGeometry,
    QgsPointXY,
    QgsFeature,
)
from qgis.analysis import QgsGraph

from ..network import ConnectivityFunction
from .routeNetwork import RouteEntry
from ..layers.routeNetworkLayer import RouteNetworkFeatureConfig
from ..helper import createDoublePointHash

class RouteNetworkAnalyser:
    def __init__(self, graph: QgsGraph, routeEntries: List[RouteEntry], config: RouteNetworkFeatureConfig = RouteNetworkFeatureConfig()):
        self.graph = graph
        self.routeEntries = routeEntries
        self.config = config
    
    def createNetworkElements(self) -> List['NetworkElement']:
        collectedEntries = {}

        class CollectedEntryItem:
            def __init__(self, edgeId: int, cf: ConnectivityFunction):
                self.edgeId = edgeId
                self.cfs = [cf]
            
            def append(self, cf: ConnectivityFunction):
                self.cfs.append(cf)

        for entry in self.routeEntries:
            if not entry.routeResult:
                continue
            for edgeId in entry.routeResult.edgeIds:
                edge = self.graph.edge(edgeId)
                v1 = self.graph.vertex(edge.fromVertex()).point()
                v2 = self.graph.vertex(edge.toVertex()).point()
                edgeKey = createDoublePointHash(v1, v2)
                if edgeKey in collectedEntries:
                    collectedEntries[edgeKey].append( entry.directRouteEntry.cf)
                else:
                    collectedEntries[edgeKey] = CollectedEntryItem(edgeId, entry.directRouteEntry.cf)
        
        # aggregate values (len, CF II len, CF III len, etc.)
        networkElements = []
        for (edgeKey, entryItem) in collectedEntries.items():
            networkElement = NetworkElement(self.graph, edgeKey, entryItem.edgeId, entryItem.cfs)
            networkElements.append(networkElement)
        
        return networkElements
    
    def aggregateElements(self, networkElements: List['NetworkElement']) -> Tuple[List['AggregatedNetworkElement'], List['BreakingElement']]:
        aggregator = NetworkAggregator(networkElements)

        return aggregator.aggregate()
        


class NetworkElement:
    def __init__(self, graph: QgsGraph, edgeKey: int, edgeId: int, cfs: List[ConnectivityFunction]) -> 'NetworkElement':
      self.edgeKey = edgeKey
      self.edgeId = edgeId
      self.cf = min(cfs, key=lambda cf: cf.value)
      self.n = len(cfs)
      self.cfMap  = { i: cfs.count(i) for i in cfs }
      edge = graph.edge(edgeId)
      self.v1Geom = graph.vertex(edge.fromVertex()).point()
      self.v2Geom = graph.vertex(edge.toVertex()).point()
      self.geom = None

    def geometry(self) -> QgsGeometry:
        if not self.geom:
            self.geom = QgsGeometry.fromPolylineXY([self.v1Geom, self.v2Geom])
        
        return self.geom
    
    def toQgsFeature(self) -> QgsFeature:
        feat = QgsFeature()
        feat.setAttributes([
            self.edgeKey,
            self.cf.asStrShort(),
            self.n,
            self.cfMap.get(ConnectivityFunction.VFS_2, 0),
            self.cfMap.get(ConnectivityFunction.VFS_3, 0),
            self.cfMap.get(ConnectivityFunction.VFS_4, 0),
        ])
        feat.setGeometry(self.geometry())

        return feat
    

class AggregatedNetworkElement:
    def __init__(self, n: int, cf: ConnectivityFunction, cfMap: Dict[ConnectivityFunction, int], geom: QgsGeometry):
        self.n = n
        self.cf = cf
        self.cfMap = cfMap
        self.geom = geom
    
    def toQgsFeature(self) -> QgsFeature:
        feat = QgsFeature()
        feat.setAttributes([
            self.cf.asStrShort(),
            self.n,
            self.cfMap.get(ConnectivityFunction.VFS_2, 0),
            self.cfMap.get(ConnectivityFunction.VFS_3, 0),
            self.cfMap.get(ConnectivityFunction.VFS_4, 0),
        ])
        feat.setGeometry(self.geom)

        return feat

class NetworkAggregator:
    def __init__(self, networkElements: List['NetworkElement']):
        self.networkElements = networkElements
        self.pointToElements = self._buildPointIndex()
        
    def _buildPointIndex(self) -> Dict[Tuple[float, float], List['NetworkElement']]:
        """Build an index of points to network elements using coordinate tuples for deterministic comparison."""
        pointIndex = defaultdict(list)
        for element in self.networkElements:
            v1Key = self._pointToKey(element.v1Geom)
            v2Key = self._pointToKey(element.v2Geom)
            pointIndex[v1Key].append(element)
            pointIndex[v2Key].append(element)
        return pointIndex
    
    def _pointToKey(self, point: QgsPointXY) -> Tuple[float, float]:
        """Convert QgsPointXY to deterministic tuple key."""
        return (point.x(), point.y())
    
    def _elementsHaveSameProperties(self, elem1: 'NetworkElement', elem2: 'NetworkElement') -> bool:
        """Check if two elements have the same properties (n and cf)."""
        return elem1.n == elem2.n and elem1.cf == elem2.cf
    
    def _areAdjacent(self, elem1: 'NetworkElement', elem2: 'NetworkElement') -> bool:
        """Check if two elements are adjacent (share a vertex) using coordinate comparison."""
        v1Key1 = self._pointToKey(elem1.v1Geom)
        v2Key1 = self._pointToKey(elem1.v2Geom)
        v1Key2 = self._pointToKey(elem2.v1Geom)
        v2Key2 = self._pointToKey(elem2.v2Geom)
        
        return (v1Key1 == v1Key2 or v1Key1 == v2Key2 or
                v2Key1 == v1Key2 or v2Key1 == v2Key2)
    
    def _getAdjacentElements(self, element: 'NetworkElement') -> List['NetworkElement']:
        """Get all elements adjacent to the given element with same properties."""
        adjacent = set()
        
        # Check elements sharing v1Geom
        v1Key = self._pointToKey(element.v1Geom)
        for other in self.pointToElements.get(v1Key, []):
            if (other.edgeKey != element.edgeKey and 
                self._elementsHaveSameProperties(element, other)):
                adjacent.add(other)
        
        # Check elements sharing v2Geom
        v2Key = self._pointToKey(element.v2Geom)
        for other in self.pointToElements.get(v2Key, []):
            if (other.edgeKey != element.edgeKey and 
                self._elementsHaveSameProperties(element, other)):
                adjacent.add(other)
        
        # Return sorted list for deterministic behavior
        return sorted(list(adjacent), key=lambda x: x.edgeKey)
    
    def _buildConnectedComponents(self) -> List[List['NetworkElement']]:
        """Build connected components of elements with same properties."""
        visited = set()
        components = []
        
        # Process elements in deterministic order
        for element in self.networkElements:
            if element.edgeKey in visited:
                continue
                
            # BFS to find all connected elements with same properties
            component = []
            queue = deque([element])
            visited.add(element.edgeKey)
            
            while queue:
                current = queue.popleft()
                component.append(current)
                
                # Get adjacent elements in deterministic order
                adjacentElements = self._getAdjacentElements(current)
                for adjacent in adjacentElements:
                    if adjacent.edgeKey not in visited:
                        visited.add(adjacent.edgeKey)
                        queue.append(adjacent)
            
            components.append(component)
        
        # Sort components for deterministic behavior
        return components
    
    def _splitComponentIntoLinearSegments(self, component: List['NetworkElement']) -> List[List['NetworkElement']]:
        """Split a component into linear segments, handling branches properly."""
        if len(component) == 1:
            return [component]
        
        # Build adjacency graph within this component only
        adjacency = {}
        for element in component:
            adjacentInComponent = []
            for other in component:
                if other.edgeKey != element.edgeKey and self._areAdjacent(element, other):
                    adjacentInComponent.append(other)
            # Sort for deterministic behavior
            adjacency[element] = adjacentInComponent
        
        # Find branch points (elements with more than 2 neighbors) and endpoints
        branchPoints = [elem for elem in component if len(adjacency[elem]) > 2]
        endpoints = [elem for elem in component if len(adjacency[elem]) <= 1]
        
        # If no branches, it's a simple linear or circular path
        if not branchPoints:
            return [component]
        
        # Find all linear segments
        segments = []
        visitedElements = set()
        
        # Start from each endpoint and branch point to find all linear segments
        startPoints = endpoints + branchPoints
        
        for startElement in sorted(startPoints, key=lambda x: x.edgeKey):
            if startElement.edgeKey in visitedElements:
                continue
            
            # For each neighbor of the start point, trace a linear segment
            for neighbor in adjacency[startElement]:
                if neighbor.edgeKey in visitedElements:
                    continue
                
                # Trace the linear segment from startElement through neighbor
                segment = self._traceLinearSegment(startElement, neighbor, adjacency, visitedElements)
                if segment and len(segment) > 0:
                    segments.append(segment)
        
        # Handle any remaining unvisited elements (shouldn't happen, but safety check)
        for element in component:
            if element.edgeKey not in visitedElements:
                segments.append([element])
                visitedElements.add(element.edgeKey)
        
        return segments
    
    def _traceLinearSegment(self, startElement: 'NetworkElement', nextElement: 'NetworkElement', 
                            adjacency: Dict, visitedElements: Set[int]) -> List['NetworkElement']:
        """Trace a linear segment from startElement through nextElement until a branch or endpoint."""
        segment = [startElement]
        visitedElements.add(startElement.edgeKey)
        
        currentElement = nextElement
        previousElement = startElement
        
        while currentElement and currentElement.edgeKey not in visitedElements:
            visitedElements.add(currentElement.edgeKey)
            segment.append(currentElement)
            
            # Find next elements (neighbors excluding the previous one)
            nextElements = [elem for elem in adjacency[currentElement] 
                           if elem.edgeKey != previousElement.edgeKey and elem.edgeKey not in visitedElements]
            
            # If there's exactly one next element, continue the linear segment
            if len(nextElements) == 1:
                previousElement = currentElement
                currentElement = nextElements[0]
            else:
                # Either endpoint (0 neighbors) or branch point (>1 neighbors) - stop tracing
                break
        
        return segment
    
    def _buildLinestringFromLinearSegment(self, segment: List['NetworkElement']) -> QgsGeometry:
        """Build a properly ordered linestring from a linear segment (no branches)."""
        if len(segment) == 1:
            return segment[0].geometry()
        
        # Build adjacency within segment
        adjacency = {}
        for element in segment:
            adjacentInSegment = []
            for other in segment:
                if other.edgeKey != element.edgeKey and self._areAdjacent(element, other):
                    adjacentInSegment.append(other)
            adjacency[element] = sorted(adjacentInSegment, key=lambda x: x.edgeKey)
        
        # Find endpoint (element with only one neighbor) or start from first element
        endpoints = [elem for elem in segment if len(adjacency[elem]) <= 1]
        startElement = endpoints[0] if endpoints else min(segment, key=lambda x: x.edgeKey)
        
        # Traverse the linear path
        pathPoints = []
        visitedElements = set()
        currentElement = startElement
        previousElement = None
        
        while currentElement and currentElement.edgeKey not in visitedElements:
            visitedElements.add(currentElement.edgeKey)
            
            if previousElement is None:
                # First element - determine orientation
                neighbors = adjacency[currentElement]
                if neighbors:
                    nextElement = neighbors[0]
                    sharedPointKey = self._getSharedPointKey(currentElement, nextElement)
                    
                    if sharedPointKey and self._pointToKey(currentElement.v1Geom) == sharedPointKey:
                        pathPoints = [currentElement.v2Geom, currentElement.v1Geom]
                    else:
                        pathPoints = [currentElement.v1Geom, currentElement.v2Geom]
                else:
                    # Single element
                    pathPoints = [currentElement.v1Geom, currentElement.v2Geom]
            else:
                # Add the point that's not shared with previous element
                sharedPointKey = self._getSharedPointKey(previousElement, currentElement)
                
                if sharedPointKey and self._pointToKey(currentElement.v1Geom) == sharedPointKey:
                    pathPoints.append(currentElement.v2Geom)
                else:
                    pathPoints.append(currentElement.v1Geom)
            
            # Move to next element
            nextElements = [elem for elem in adjacency[currentElement] 
                           if previousElement is None or elem.edgeKey != previousElement.edgeKey]
            nextElements = [elem for elem in nextElements if elem.edgeKey not in visitedElements]
            
            previousElement = currentElement
            currentElement = nextElements[0] if nextElements else None
        
        return QgsGeometry.fromPolylineXY(pathPoints)
    
    def _getSharedPointKey(self, elem1: 'NetworkElement', elem2: 'NetworkElement') -> Optional[Tuple[float, float]]:
        """Get the shared point key between two adjacent elements."""
        v1Key1 = self._pointToKey(elem1.v1Geom)
        v2Key1 = self._pointToKey(elem1.v2Geom)
        v1Key2 = self._pointToKey(elem2.v1Geom)
        v2Key2 = self._pointToKey(elem2.v2Geom)
        
        if v1Key1 == v1Key2 or v1Key1 == v2Key2:
            return v1Key1
        elif v2Key1 == v1Key2 or v2Key1 == v2Key2:
            return v2Key1
        return None
    
    def aggregate(self) -> Tuple[List[AggregatedNetworkElement], List['BreakingElement']]:
        """
        Aggregate network elements and extract breaking points.
        
        Returns:
            Tuple of (aggregatedElements, breakingPoints)
        """
        components = self._buildConnectedComponents()
        aggregatedElements = []
        processedElements = set()
        
        for component in components:
            if not component:
                continue
            
            # Split component into linear segments to handle branches
            linearSegments = self._splitComponentIntoLinearSegments(component)
            
            for segment in linearSegments:
                if not segment:
                    continue
                
                # Use properties from first element (all should be the same)
                firstElement = segment[0]
                n = firstElement.n
                cf = firstElement.cf
                cfMap = firstElement.cfMap
                
                # Build linestring geometry for this linear segment
                geom = self._buildLinestringFromLinearSegment(segment)
                
                aggregatedElements.append(AggregatedNetworkElement(n, cf, cfMap, geom))
                
                # Track processed elements
                for elem in segment:
                    processedElements.add(elem.edgeKey)
        

        breakingPoints = self.extractBreakingPoints(aggregatedElements)
        (aggregatedElements, breakingPoints) = self._breakAggregationElements(aggregatedElements, breakingPoints)
        
        return (aggregatedElements, breakingPoints)
    
    def extractBreakingPoints(self, aggregatedElements: List[AggregatedNetworkElement]) -> List['BreakingElement']:
        """
        Extract breaking points where linestrings touch but don't continue.
        """
        breakingElements = {}

        def addToBreaking(point: QgsPointXY, pointIndex: int, aggElem: AggregatedNetworkElement, isStartEnd: bool):
            key = self._pointToKey(point)
            if key in breakingElements:
                breakingElements[key].merge(pointIndex, aggElem, isStartEnd)
            else:
                breakingElements[key] = BreakingElement(point, pointIndex, 1, aggElem, isStartEnd)

        for aggElem in aggregatedElements:
            polyline = aggElem.geom.asPolyline()
            
            addToBreaking(polyline[0], 0, aggElem, True)
            for (i, point) in enumerate(polyline[1:-1]):
                addToBreaking(point, i + 1, aggElem, False)
            addToBreaking(polyline[-1], len(polyline) - 1, aggElem, True)
        
        # Breaking points are where multiple linestrings meet (count > 1)
        breakingPointElements = []
        nonBreakingPointElements = []
        for breakingElement in breakingElements.values():
            if breakingElement.count > 1:
                breakingPointElements.append(breakingElement)
            else:
                nonBreakingPointElements.append(breakingElement)
        breakingPointElements = [value for value in breakingElements.values() if value.count > 1]
        
        return breakingPointElements
    
    def _breakAggregationElements(self, aggregatedElements: List[AggregatedNetworkElement], breakingElements: List['BreakingElement']) -> Tuple[List[AggregatedNetworkElement], List['SealedBreakingElement']]:
        aggregationsToSplit = defaultdict(list)
        sealedBreakingElements = []

        for breakingElement in breakingElements:
            if breakingElement.count > 1:
                sealedBreakingElements.append(SealedBreakingElement(breakingElement))
                for i in range(0, len(breakingElement.pointIndices)):
                    aggregationsToSplit[breakingElement.sourceElements[i]].append(breakingElement.pointIndices[i])
        
        splittedAggregations = set()
        for (aggregation, breakIndices) in aggregationsToSplit.items():
            breakIndices.sort()
            fromIndex = 0
            basePolyline = aggregation.geom.asPolyline()
            for breakIndex in breakIndices:
                splittedGeom = QgsGeometry.fromPolylineXY(basePolyline[fromIndex:breakIndex + 1])
                splittedAggregations.add(AggregatedNetworkElement(aggregation.n, aggregation.cf, aggregation.cfMap, splittedGeom))
                fromIndex = breakIndex
            splittedGeom = QgsGeometry.fromPolylineXY(basePolyline[fromIndex:])
            splittedAggregations.add(AggregatedNetworkElement(aggregation.n, aggregation.cf, aggregation.cfMap, splittedGeom))
        
            aggregatedElements.remove(aggregation)
        
        aggregatedElements += splittedAggregations

        return (aggregatedElements, sealedBreakingElements)
        


class BreakingElement:
    def __init__(self, geom: QgsPointXY, pointIndex: int, count: int, aggregationElement: AggregatedNetworkElement, isStartEnd: bool):
        self.count = count
        self.n = aggregationElement.n
        self.cf = aggregationElement.cf
        self.cfMap = aggregationElement.cfMap
        if isStartEnd:
            self.sourceElements = []
            self.pointIndices = []
        else:
            self.sourceElements = [aggregationElement]
            self.pointIndices = [pointIndex]
        self.geom = geom
    
    def merge(self, pointIndex: int, aggregationElement: AggregatedNetworkElement, isStartEnd: bool):
        self.count += 1
        if not isStartEnd:
            self.sourceElements.append(aggregationElement)
            self.pointIndices.append(pointIndex)
        
        self.cf = ConnectivityFunction.getLowerCF(self.cf, aggregationElement.cf)
        if self.n < aggregationElement.n:
            self.cfMap = aggregationElement.cfMap
    
    def toQgsFeature(self) -> QgsFeature:
        feat = QgsFeature()
        feat.setAttributes([
            self.cf.asStrShort(),
            self.n,
            self.cfMap.get(ConnectivityFunction.VFS_2, 0),
            self.cfMap.get(ConnectivityFunction.VFS_3, 0),
            self.cfMap.get(ConnectivityFunction.VFS_4, 0),
        ])
        feat.setGeometry(QgsGeometry.fromPointXY(self.geom))

        return feat

class SealedBreakingElement:
    def __init__(self, breakingElement: BreakingElement) -> 'SealedBreakingElement':
        self.n = breakingElement.n
        self.cf = breakingElement.cf
        self.cfMap = breakingElement.cfMap
        self.geom = breakingElement.geom

    def toQgsFeature(self) -> QgsFeature:
        feat = QgsFeature()
        feat.setAttributes([
            self.cf.asStrShort(),
            self.n,
            self.cfMap.get(ConnectivityFunction.VFS_2, 0),
            self.cfMap.get(ConnectivityFunction.VFS_3, 0),
            self.cfMap.get(ConnectivityFunction.VFS_4, 0),
        ])
        feat.setGeometry(QgsGeometry.fromPointXY(self.geom))

        return feat