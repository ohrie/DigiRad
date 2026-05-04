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

from typing import List

from qgis.core import (
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
        if "epsg" not in providerUrl.lower():
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
