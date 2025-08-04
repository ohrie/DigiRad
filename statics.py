# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Statics
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

import os

from qgis.core import QgsVectorLayer

from .constants import DAT_PATH
from .classes.ars import ARSIndex
from .classes.processingConfig import ProcessingConfig
from .classes.layerManager import LayerManager
from .classes.processing.networkValidator import Networkvalidator

ARS_INDEX = ARSIndex(os.path.join(DAT_PATH, "ARS_Zentren_merged.csv"))
PROCESSING_CONFIG = ProcessingConfig()
LAYER_MANAGER = LayerManager(PROCESSING_CONFIG.projectName)

NETWORK_VALIDATOR = Networkvalidator(LAYER_MANAGER.crs())