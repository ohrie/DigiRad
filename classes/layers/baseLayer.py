# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BaseLayer
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

from typing import Self

from qgis.core import (
    QgsMessageLog,
    QgsRasterLayer,
)

from .layer import DigiRadLayer

class BaseLayer(DigiRadLayer):
    LayerName = "Hintergrundkarte"

    def __init__(self, wmsLayer: QgsRasterLayer):
        super().__init__(wmsLayer)

    def create() -> Self:
        tms = "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=16"
        layer = QgsRasterLayer(tms, BaseLayer.LayerName, "wms")
        return BaseLayer(layer)