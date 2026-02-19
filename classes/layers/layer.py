# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DigiRadLayer
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

from abc import ABC
from typing import Optional, List
from qgis.core import QgsVectorLayer, QgsMessageLog

class DigiRadLayer(ABC):
    """Base class for digirad layers"""

    def __init__(self, qgslayer: QgsVectorLayer, groupName: str = None, visible: bool = True, expanded: bool = True):
        self._qgsLayer = qgslayer
        self.groupName = groupName
        self.visible = visible
        self.expanded = expanded
    
    def qgsLayer(self) -> Optional[QgsVectorLayer]:
        return self._qgsLayer
    
    def name(self) -> Optional[str]:
        try:
            id = self._qgsLayer.name()
        except:
            return None
        return id
    
    def id(self) -> Optional[int]:
        try:
            id = self._qgsLayer.id()
        except:
            return None
        return id
    
    def isQgsLayerPresent(self) -> bool:
        return self.id() is not None