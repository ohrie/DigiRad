# -*- coding: utf-8 -*-
"""
/***************************************************************************
RouteNetworkTaskHelpers
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
from typing import List, Optional

from .routeNetwork import RouteEntry
from .routeNetworkAnalyser import NetworkElement, AggregatedNetworkElement, BreakingElement

class RouteNetworkTaskResult:
    def __init__(self, routeEntries: Optional[List[RouteEntry]] = None, networkElements: Optional[List[NetworkElement]] = None, aggregatedElements: Optional[List[AggregatedNetworkElement]] = None, breakingPoints:Optional[ List[BreakingElement]] = None, error: str = None):
        self.routeEntries = routeEntries
        self.networkElements = networkElements
        self.aggregatedElements = aggregatedElements
        self.breakingPoints = breakingPoints
        self.error = error
    
    def isError(self) -> bool:
        return self.error is not None

    @staticmethod
    def createSuccess(routeEntries: List[RouteEntry], networkElements: List[NetworkElement], aggregatedElements: List[AggregatedNetworkElement], breakingPoints: List[BreakingElement]) -> 'RouteNetworkTaskResult':
        return RouteNetworkTaskResult(routeEntries=routeEntries, networkElements=networkElements, aggregatedElements=aggregatedElements, breakingPoints=breakingPoints)
    
    @staticmethod
    def createError(errorMessage: str) -> 'RouteNetworkTaskResult':
        return RouteNetworkTaskResult(error=errorMessage)

class RouteNetworkTaskProgress():
    def __init__(self, progress: int, message: str = ""):
        self.progress = progress
        self.message = message
    
    def isDifferentTo(self, other: 'RouteNetworkTaskProgress') -> bool:
        return self.progress != other.progress or self.message != other.message