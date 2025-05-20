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
from .classes.ars import ARSIndex
from .classes.processingConfig import ProcessingConfig
from .classes.layerManager import LayerManager

PLUGIN_PATH = os.path.dirname(os.path.realpath(__file__))
DAT_PATH = os.path.join(PLUGIN_PATH, "dat")

DUMMY_CENTER_OGR_PATH = os.path.join("C:/Users/Lindemann/Documents/Arbeit/VV/Projekte/2025/2_DigiRad/4_Daten/Kommunen", "Dummy_Dresden_Zentren.gpkg")

ARS_INDEX = ARSIndex(os.path.join(DAT_PATH, "ARS_Zentren_VG_Kreise.csv"))
PROCESSING_CONFIG = ProcessingConfig()
LAYER_MANAGER = LayerManager(PROCESSING_CONFIG.projectName)