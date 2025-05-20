# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Helper
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

from qgis.core import QgsPoint

def createPointHash(point: QgsPoint) -> int:
    return hash((point.x(), point.y()))

def createDoublePointHash(point1: QgsPoint, point2: QgsPoint) -> int:
    minX = min(point1.x(), point2.x())
    minY = min(point1.y(), point2.y())
    maxX = max(point1.x(), point2.x())
    maxY = max(point1.y(), point2.y())
    return hash((minX, minY, maxX, maxY))