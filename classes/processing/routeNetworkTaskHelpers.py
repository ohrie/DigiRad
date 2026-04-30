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

from typing import List, Optional

from .routeNetwork import RouteEntry
from .routeNetworkAnalyser import NetworkElement, AggregatedNetworkElement, BreakingElement
from .directRouteEntry import DirectRouteEntry

class RouteNetworkTaskResult:
    def __init__(self, routeEntries: Optional[List[RouteEntry]] = None, networkElements: Optional[List[NetworkElement]] = None, aggregatedElements: Optional[List[AggregatedNetworkElement]] = None, breakingPoints:Optional[ List[BreakingElement]] = None, error: str = None):
        self.routeEntries = routeEntries
        self.networkElements = networkElements
        self.aggregatedElements = aggregatedElements
        self.breakingPoints = breakingPoints
        self.error = error
    
    def isError(self) -> bool:
        return self.error is not None
    
    def getMissingRoutes(self) -> List[DirectRouteEntry]:
        return [r.directRouteEntry for r in self.routeEntries if r.notFound()]

    @staticmethod
    def createSuccess(
        routeEntries: List[RouteEntry],
        networkElements: List[NetworkElement],
        aggregatedElements: List[AggregatedNetworkElement],
        breakingPoints: List[BreakingElement]) -> 'RouteNetworkTaskResult':
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