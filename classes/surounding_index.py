# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SuroundingIndex
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
from typing import List, Dict, Optional
from qgis.core import (
    QgsMessageLog,
    QgsVectorLayer,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsFeatureRequest,
    QgsPoint,
    QgsSymbol,
    QgsWkbTypes,
    QgsEditFormConfig,
    QgsAttributeEditorField,
    QgsEditorWidgetSetup
)

from .ars import ARSCodeStr

class SuroundingIndex:
    def __init__(self, sourceLayerPath: str):
        self.layer = QgsVectorLayer(sourceLayerPath, "suroundings_index", "ogr")
    
    

class SuroundingCenterFeature:
    def __init__(geom: QgsPoint, self, ars: ARSCodeStr, name: str = ""):
        self.geom = geom
        self.ars = ars
        self.name = name