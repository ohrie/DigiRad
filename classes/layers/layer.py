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

from abc import ABC
from typing import Optional
from qgis.core import QgsVectorLayer


class DigiRadLayer(ABC):
    """Base class for digirad layers"""

    def __init__(self, qgslayer: QgsVectorLayer, groupName: str = None,
                 visible: bool = True, expanded: bool = True):
        self._qgsLayer = qgslayer
        self.groupName = groupName
        self.visible = visible
        self.expanded = expanded

    def qgsLayer(self) -> Optional[QgsVectorLayer]:
        return self._qgsLayer

    def name(self) -> Optional[str]:
        try:
            id = self._qgsLayer.name()
        except BaseException:
            return None
        return id

    def id(self) -> Optional[int]:
        try:
            id = self._qgsLayer.id()
        except BaseException:
            return None
        return id

    def isQgsLayerPresent(self) -> bool:
        return self.id() is not None
