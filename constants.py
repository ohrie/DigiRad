# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Constants
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

PLUGIN_PATH = os.path.dirname(os.path.realpath(__file__))
DAT_PATH = os.path.join(PLUGIN_PATH, "dat")

AUTO_CENTER_POINTS_PATH = os.path.join(DAT_PATH, "DigiRadAutoZentren.gpkg")

EPSG_CODE = "25832"
CRS_STR = "EPSG:{}".format(EPSG_CODE)