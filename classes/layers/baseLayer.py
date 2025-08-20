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

from typing import List

from qgis.core import (
    QgsMessageLog,
    QgsRasterLayer,
    QgsCoordinateReferenceSystem,
)

from .layer import DigiRadLayer

class BaseLayer(DigiRadLayer):
    LayerName = "Hintergrundkarte"

    def __init__(self, wmsLayer: QgsRasterLayer):
        super().__init__(wmsLayer)

    def create(providerUrl: str) -> 'BaseLayer':
        if not providerUrl:
            providerUrl = BaseLayerProvider.Layers["Openstreetmap (Standard)"]
        layer = QgsRasterLayer(providerUrl, BaseLayer.LayerName, "wms")
        if not "epsg" in providerUrl.lower():
            layer.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
        return BaseLayer(layer)
    
    def createFromProviderName(providerName: str) -> 'BaseLayer':
        if providerName in BaseLayerProvider.Layers:
            return BaseLayer.create(BaseLayerProvider.Layers[providerName])
        else:
            return BaseLayer.create()

class BaseLayerProvider:
    Layers = {
        "Openstreetmap (Standard)": ("type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png"),
        "TopPlusOpen": "crs=EPSG:25832&dpiMode=7&format=image/png&layers=web&styles&tilePixelRatio=0&url=https://sgx.geodatenzentrum.de/wms_topplus_open",
        "TopPlusOpen (Graustufen)": "crs=EPSG:25832&dpiMode=7&format=image/png&layers=web_grau&styles&tilePixelRatio=0&url=https://sgx.geodatenzentrum.de/wms_topplus_open",
        "TopPlusOpen (Light)": "crs=EPSG:25832&dpiMode=7&format=image/png&layers=web_light_grau&styles&tilePixelRatio=0&url=https://sgx.geodatenzentrum.de/wms_topplus_open" 
    }
    
    @staticmethod
    def getLayerNames() -> List[str]:
        return list(BaseLayerProvider.Layers.keys())