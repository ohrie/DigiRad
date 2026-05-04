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

from qgis.core import QgsVectorLayer, QgsCategorizedSymbolRenderer, QgsMarkerSymbol, QgsRendererCategory


class CenterLayer():
    def __init__(self, layer):
        renderer = self._createRenderer()
        layer.setRenderer(renderer)
        layer.triggerRepaint()

        self._layer = layer

    def _createRenderer(
            self, categoryField: str = "Centertype") -> QgsCategorizedSymbolRenderer:
        renderer = QgsCategorizedSymbolRenderer(categoryField)

        # Define your categories with their styles
        # Format: CenterType value, Symbol (color and size), Label
        categories = [
            ["Oberzentru", QgsMarkerSymbol.createSimple(
                {'color': '0,0,255', 'size': '4'}), "Oberzentrum"],
            ["Grundzentr", QgsMarkerSymbol.createSimple(
                {'color': '255,0,0', 'size': '2'}), "Grundzentrum"],
        ]
        for category in categories:
            value = category[0]
            symbol = category[1]
            label = category[2]

            cat = QgsRendererCategory(value, symbol, label)
            renderer.addCategory(cat)

        return renderer

    @staticmethod
    def loadFromFile(filePath: str, layerName):
        layer = QgsVectorLayer(filePath, layerName, "ogr")
        return CenterLayer(layer)

    def qgsLayer(self):
        return self._layer

    def name(self):
        return self._layer.name()
