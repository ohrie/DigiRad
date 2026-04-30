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

import os

from qgis.core import QgsVectorLayer

PLUGIN_PATH = os.path.dirname(os.path.realpath(__file__))
DAT_PATH = os.path.join(PLUGIN_PATH, "dat")

AUTO_CENTER_POINTS_PATH = os.path.join(DAT_PATH, "DigiRadAutoZentren.gpkg")

REPROJECT_DETOUR_FACTOR = 0.3

EPSG_CODE = "25832"
CRS_STR = "EPSG:{}".format(EPSG_CODE)
# Surrounding distance in m
SURROUNDING_QUERY_DISTANCE = 25000
SURROUNDINGS_CENTER_POINTS_PATH = os.path.join(DAT_PATH, "DigiRadUmgebungsgemeinden.gpkg")
SURROUNDING_LAYER = QgsVectorLayer(SURROUNDINGS_CENTER_POINTS_PATH, "suroundings_index", "ogr")