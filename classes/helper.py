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

from qgis.core import QgsPoint

def createPointHash(point: QgsPoint) -> int:
    return hash((point.x(), point.y()))

def createDoublePointHash(point1: QgsPoint, point2: QgsPoint) -> int:
    minX = min(point1.x(), point2.x())
    minY = min(point1.y(), point2.y())
    maxX = max(point1.x(), point2.x())
    maxY = max(point1.y(), point2.y())
    return hash((minX, minY, maxX, maxY))