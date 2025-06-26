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
from typing import Self, List, Set, Dict, Tuple, Optional
from collections import defaultdict, deque

from PyQt5.QtCore import QVariant
from qgis.core import (
    QgsMessageLog,
    QgsGeometry,
    QgsPointXY,
    QgsFeature,
    QgsVectorLayer,
    QgsField,
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
    
    def createNetworkElements(self) -> List['AggregatedNetworkElement']:
        collectedEntries = {}

        class CollectedEntryItem:
            def __init__(self, edgeId: int, cf: ConnectivityFunction):
                self.edgeId = edgeId
                self.cfs = [cf]
            
            def append(self, cf: ConnectivityFunction):
                self.cfs.append(cf)

        for entry in self.routeEntries:
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
        
        aggregator = NetworkAggregator(networkElements)
        (aggregatedElements, breakingPoints) = aggregator.aggregate()
        # aggregator.debug_aggregation()
        QgsMessageLog.logMessage(f"LEEEE {len(aggregatedElements)}")
        QgsMessageLog.logMessage(f"BREA {len(breakingPoints)}")
        
        return (networkElements, aggregatedElements)

        # create geoemtries for edge edgeId
        # combine adjacent geometries with same values
        # create qgs features
        #  


class NetworkElement:
    def __init__(self, graph: QgsGraph, edgeKey: int, edgeId: int, cfs: List[ConnectivityFunction]) -> Self:
      self.edgeKey = edgeKey
      self.edgeId = edgeId
      self.cf = min(cfs, key=lambda cf: cf.value)
      self.n = len(cfs)
      self.cfMap  = { i: cfs.count(i) for i in cfs }
      edge = graph.edge(edgeId)
      self.v1Geom = graph.vertex(edge.fromVertex()).point()
      self.v2Geom = graph.vertex(edge.toVertex()).point()
      self._geom = None

    def geometry(self) -> QgsGeometry:
        if not self._geom:
            self._geom = QgsGeometry.fromPolylineXY([self.v1Geom, self.v2Geom])
        
        return self._geom
    
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
    def __init__(self, n: int, cf, cfMap, geom: QgsGeometry):
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
    def __init__(self, network_elements: List['NetworkElement']):
        self.network_elements = network_elements
        self.point_to_elements = self._build_point_index()
        
    def _build_point_index(self) -> Dict[QgsPointXY, List['NetworkElement']]:
        """Build an index of points to network elements for efficient adjacency lookup."""
        point_index = defaultdict(list)
        for element in self.network_elements:
            if element.edgeKey == 3056687759621442214:
                QgsMessageLog.logMessage(f"BEFORE {len(point_index)}")
            point_index[element.v1Geom].append(element)
            point_index[element.v2Geom].append(element)
            if element.edgeKey == 3056687759621442214:
                QgsMessageLog.logMessage(f"AFTER {len(point_index)}")
        return point_index
    
    def _elements_have_same_properties(self, elem1: 'NetworkElement', elem2: 'NetworkElement') -> bool:
        """Check if two elements have the same properties (n and cf)."""
        return elem1.n == elem2.n and elem1.cf == elem2.cf
    
    def _are_adjacent(self, elem1: 'NetworkElement', elem2: 'NetworkElement') -> bool:
        """Check if two elements are adjacent (share a vertex)."""
        return (elem1.v1Geom == elem2.v1Geom or elem1.v1Geom == elem2.v2Geom or
                elem1.v2Geom == elem2.v1Geom or elem1.v2Geom == elem2.v2Geom)
    
    def _get_adjacent_elements(self, element: 'NetworkElement') -> List['NetworkElement']:
        """Get all elements adjacent to the given element with same properties."""
        adjacent = set()  # Use set to avoid duplicates
        
        # Check elements sharing v1Geom
        for other in self.point_to_elements[element.v1Geom]:
            if (other != element and 
                self._elements_have_same_properties(element, other)):
                adjacent.add(other)
        
        # Check elements sharing v2Geom
        for other in self.point_to_elements[element.v2Geom]:
            if (other != element and 
                self._elements_have_same_properties(element, other)):
                adjacent.add(other)
        
        if element.edgeKey == 3056687759621442214:
            QgsMessageLog.logMessage(f"adja element empty list: {len(list(adjacent))}")

        if element.edgeKey == -3887448145531821601:
            QgsMessageLog.logMessage(f"adja element f list: {len(list(adjacent))}")
        
        return list(adjacent)
    
    def _build_connected_components(self) -> List[List['NetworkElement']]:
        """Build connected components of elements with same properties."""
        visited = set()
        components = []
        
        for element in self.network_elements:
            if element.edgeKey == 3056687759621442214:
                QgsMessageLog.logMessage(f"looking at element")
            if element in visited:
                continue
            if element.edgeKey == 3056687759621442214:
                QgsMessageLog.logMessage(f"processing element")

            # BFS to find all connected elements with same properties
            component = []
            queue = deque([element])
            visited.add(element)
            
            while queue:
                current = queue.popleft()
                component.append(current)
                
                for adjacent in self._get_adjacent_elements(current):
                    if adjacent not in visited:
                        visited.add(adjacent)
                        queue.append(adjacent)
            
            components.append(component)
        
        return components
    
    def _build_linestring_from_component(self, component: List['NetworkElement']) -> QgsGeometry:
        """Build a properly ordered linestring from a connected component."""
        if len(component) == 1:
            if component[0].edgeKey == 3056687759621442214:
                QgsMessageLog.logMessage(f"single geom")
            return component[0].geometry()
        
        # Build adjacency graph within this component only
        adjacency = {}
        for element in component:
            if element.edgeKey == 3056687759621442214:
                QgsMessageLog.logMessage(f"YES")
            adjacent_in_component = []
            for other in component:
                if other != element and self._are_adjacent(element, other):
                    adjacent_in_component.append(other)
            adjacency[element] = adjacent_in_component
        
        # Find endpoints (elements with only one neighbor) or start points
        endpoints = [elem for elem in component if len(adjacency[elem]) <= 1]
        
        if not endpoints:
            # Handle circular case - start from any element
            start_element = component[0]
        else:
            start_element = endpoints[0]
        
        # Traverse the path
        path_points = []
        visited_elements = set()
        current_element = start_element
        previous_element = None
        
        # Add first element's points
        if len(adjacency[current_element]) == 0:
            # Isolated element
            path_points = [current_element.v1Geom, current_element.v2Geom]
            if current_element.edgeKey == 3056687759621442214:
                QgsMessageLog.logMessage(f"1")
            visited_elements.add(current_element)
        else:
            # Start traversal
            next_element = adjacency[current_element][0]
            shared_point = self._get_shared_point(current_element, next_element)
            
            if current_element.v1Geom == shared_point:
                path_points = [current_element.v2Geom, current_element.v1Geom]
            else:
                path_points = [current_element.v1Geom, current_element.v2Geom]
            
            if current_element.edgeKey == 3056687759621442214:
                QgsMessageLog.logMessage(f"2")
            visited_elements.add(current_element)
            previous_element = current_element
            current_element = next_element
        
        # Continue traversal
        while current_element and current_element not in visited_elements:
            if current_element.edgeKey == 3056687759621442214:
                QgsMessageLog.logMessage(f"trave")
            visited_elements.add(current_element)
            
            # Find the point that connects to previous element
            shared_point = self._get_shared_point(previous_element, current_element)
            
            # Add the other point
            if current_element.v1Geom == shared_point:
                path_points.append(current_element.v2Geom)
            else:
                path_points.append(current_element.v1Geom)
            
            # Move to next element
            next_elements = [elem for elem in adjacency[current_element] 
                           if elem != previous_element and elem not in visited_elements]
            
            previous_element = current_element
            current_element = next_elements[0] if next_elements else None
        
        return QgsGeometry.fromPolylineXY(path_points)
    
    def _get_adjacent_elements_in_component(self, element: 'NetworkElement', 
                                          component: List['NetworkElement']) -> List['NetworkElement']:
        """Get adjacent elements within a specific component."""
        adjacent = self._get_adjacent_elements(element)
        return [elem for elem in adjacent if elem in component]
    
    def _get_shared_point(self, elem1: 'NetworkElement', elem2: 'NetworkElement') -> Optional[QgsPointXY]:
        """Get the shared point between two adjacent elements."""
        if elem1.v1Geom == elem2.v1Geom or elem1.v1Geom == elem2.v2Geom:
            return elem1.v1Geom
        elif elem1.v2Geom == elem2.v1Geom or elem1.v2Geom == elem2.v2Geom:
            return elem1.v2Geom
        return None
    
    def aggregate(self) -> Tuple[List[AggregatedNetworkElement], List[QgsPointXY]]:
        """
        Aggregate network elements and extract breaking points.
        
        Returns:
            Tuple of (aggregated_elements, breaking_points)
        """
        components = self._build_connected_components()
        aggregated_elements = []
        processed_elements = set()
        
        for component in components:
            if not component:
                continue
                
            # Use properties from first element (all should be the same)
            first_element = component[0]
            n = first_element.n
            cf = first_element.cf
            cfMap = first_element.cfMap
            
            # Build linestring geometry
            geom = self._build_linestring_from_component(component)
            
            aggregated_elements.append(AggregatedNetworkElement(n, cf,cfMap, geom))
            
            # Track processed elements
            for elem in component:
                processed_elements.add(elem)
        
        # Verify all elements were processed
        missing_elements = set(self.network_elements) - processed_elements
        if missing_elements:
            print(f"Warning: {len(missing_elements)} elements were not processed!")
            for elem in missing_elements:
                print(f"Missing element: edgeKey={elem.edgeKey}, n={elem.n}, cf={elem.cf}")
                # Add as individual elements
                aggregated_elements.append(AggregatedNetworkElement(elem.n, elem.cf, elem.geometry()))
        
        # Extract breaking points
        breaking_points = self._extract_breaking_points(aggregated_elements)
        
        return aggregated_elements, breaking_points
    
    def _extract_breaking_points(self, aggregated_elements: List[AggregatedNetworkElement]) -> List[QgsPointXY]:
        """
        Extract breaking points where linestrings touch but don't continue.
        These are endpoints of linestrings that coincide with endpoints of other linestrings.
        """
        # Collect all endpoints
        endpoint_counts = defaultdict(int)
        
        for agg_elem in aggregated_elements:
            polyline = agg_elem.geom.asPolyline()
            if len(polyline) >= 2:
                endpoint_counts[polyline[0]] += 1  # Start point
                endpoint_counts[polyline[-1]] += 1  # End point
        
        # Breaking points are where multiple linestrings meet (count > 1)
        breaking_points = [point for point, count in endpoint_counts.items() if count > 1]
        
        return breaking_points

    def debug_aggregation(self) -> None:
        """Debug method to print aggregation details."""
        QgsMessageLog.logMessage(f"Total network elements: {len(self.network_elements)}")
        
        # Check property groupings
        property_groups = defaultdict(list)
        for elem in self.network_elements:
            key = (elem.n, elem.cf)
            property_groups[key].append(elem)
        
        QgsMessageLog.logMessage(f"Property groups: {len(property_groups)}")
        for key, elements in property_groups.items():
            QgsMessageLog.logMessage(f"  Group {key}: {len(elements)} elements")
        
        # Check connectivity
        components = self._build_connected_components()
        QgsMessageLog.logMessage(f"Connected components: {len(components)}")
        total_in_components = sum(len(comp) for comp in components)
        QgsMessageLog.logMessage(f"Elements in components: {total_in_components}")
        
        for i, component in enumerate(components):
            if component:
                first = component[0]
                QgsMessageLog.logMessage(f"  Component {i}: {len(component)} elements, n={first.n}, cf={first.cf}")
