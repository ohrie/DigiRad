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

from qgis.core import QgsDistanceArea, QgsCoordinateReferenceSystem, QgsCoordinateTransformContext

from ...constants import CRS_STR

class ValidationEntry:
    def __init__(self, airDistPathRel):
        self.airDistPathRel = airDistPathRel
    
    @staticmethod
    def empty() -> 'ValidationEntry':
        ValidationEntry(0)
    
    def isEmpty(self) -> bool:
        return self.airDistPathRel == 0

class NetworkvalidatorMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__()
            cls._instances[cls] = instance
        return cls._instances[cls]

class Networkvalidator(metaclass=NetworkvalidatorMeta):
    def __init__(self):
        distCalc = QgsDistanceArea()
        distCalc.setSourceCrs(QgsCoordinateReferenceSystem(CRS_STR), QgsCoordinateTransformContext())
        distCalc.setEllipsoid('WGS84')
        
        self.distCalc = distCalc

    def validate(self, routeEntry) -> ValidationEntry:
        if routeEntry.notFound():
            return ValidationEntry.empty()
        airDistPathRel = self._calculateAirDistPathRel(routeEntry)
        return ValidationEntry(airDistPathRel)
    
    def _calculateAirDistPathRel(self, routeEntry) -> float:
        airDistance = self.distCalc.measureLength(routeEntry.directRouteEntry.geometry())
        pathDistance = self.distCalc.measureLength(routeEntry.geometry())

        return pathDistance / airDistance