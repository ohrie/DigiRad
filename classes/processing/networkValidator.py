# -*- coding: utf-8 -*-
"""
/***************************************************************************
NetworkValidator
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

from qgis.core import QgsDistanceArea, QgsCoordinateReferenceSystem, QgsCoordinateTransformContext

from ...constants import CRS_STR

class ValidationEntry:
    def __init__(self, detourFactor):
        self.detourFactor = detourFactor
    
    @staticmethod
    def empty() -> 'ValidationEntry':
        ValidationEntry(0)
    
    def isEmpty(self) -> bool:
        return self.detourFactor == 0

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
        detourFactor = self._calculateDetourFactor(routeEntry)
        return ValidationEntry(detourFactor)
    
    def _calculateDetourFactor(self, routeEntry) -> float:
        airDistance = self.distCalc.measureLength(routeEntry.directRouteEntry.geometry())
        pathDistance = self.distCalc.measureLength(routeEntry.geometry())

        return pathDistance / airDistance