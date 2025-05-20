# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ProcessingConfig
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

from datetime import datetime

from .ars import ARSCode

class ProcessingConfig:
    def __init__(self):
        self.projectName = "DigiRad"
        self.arsCode = None
    
    def setARSCode(self, arsCode: ARSCode):
        self.arsCode = arsCode
        dt = datetime.today().strftime('%Y-%m-%d')
        self.projectName = f"{arsCode.name}_{dt}"