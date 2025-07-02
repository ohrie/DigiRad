# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Network
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

from typing import List, TypeVar
from enum import Enum

CF = TypeVar('CF', bound='ConnectivityFunction')
LOC = TypeVar('LOC', bound='LevelOfCentrality')

class ConnectivityFunction(Enum):
    VFS_1 = 1
    VFS_2 = 2
    VFS_3 = 3
    VFS_4 = 4
    VFS_5 = 5

    @staticmethod
    def defaults() -> List['ConnectivityFunction']:
        return [ConnectivityFunction.VFS_2, ConnectivityFunction.VFS_3, ConnectivityFunction.VFS_4]
    
    def asStr(self) -> str:
        if self == ConnectivityFunction.VFS_1:
            return "Verbindungsfunktionsstufe I"
        elif self == ConnectivityFunction.VFS_2:
            return "Verbindungsfunktionsstufe II"
        elif self == ConnectivityFunction.VFS_3:
            return "Verbindungsfunktionsstufe III"
        elif self == ConnectivityFunction.VFS_4:
            return "Verbindungsfunktionsstufe IV"
        elif self == ConnectivityFunction.VFS_5:
            return "Verbindungsfunktionsstufe V"
    
    def asStrShort(self) -> str:
        if self == ConnectivityFunction.VFS_1:
            return "VFS I"
        elif self == ConnectivityFunction.VFS_2:
            return "VFS II"
        elif self == ConnectivityFunction.VFS_3:
            return "VFS III"
        elif self == ConnectivityFunction.VFS_4:
            return "VFS IV"
        elif self == ConnectivityFunction.VFS_5:
            return "VFS V"
    
    def isLowerEq(self, other: 'ConnectivityFunction') -> bool:
        return self.value <= other.value
    
    def isHigherEq(self, other: 'ConnectivityFunction') -> bool:
        return self.value >= other.value
    
    @staticmethod
    def getLowerCF(value1: 'ConnectivityFunction', value2: 'ConnectivityFunction') -> 'ConnectivityFunction':
        return ConnectivityFunction(min(value1.value, value2.value))
    
    @staticmethod
    def getUpperCF(value1: 'ConnectivityFunction', value2: 'ConnectivityFunction') -> 'ConnectivityFunction':
        return ConnectivityFunction(max(value1.value, value2.value))

class LevelOfCentrality(Enum):
    II = 2
    III = 3
    IV = 4
    Singular = 10

    @staticmethod
    def defaults() -> List['LevelOfCentrality']:
        return [LevelOfCentrality.II, LevelOfCentrality.III, LevelOfCentrality.IV, LevelOfCentrality.Singular]

    @staticmethod
    def fromStr(value: str) -> 'LevelOfCentrality':
        value = value.lower()
        if value == "zentralitätsstufe ii":
            return LevelOfCentrality.II
        elif value == "zentralitätsstufe iii":
            return LevelOfCentrality.III
        elif value == "zentralitätsstufe iv":
            return LevelOfCentrality.IV
        elif value == "singulärer erzeuger":
            return LevelOfCentrality.Singular
        else:
            raise ValueError(f"'{value}' is not a valid level of centrality")
    
    def asStr(self) -> str:
        if self == LevelOfCentrality.II:
            return "Zentralitätsstufe II"
        elif self == LevelOfCentrality.III:
            return "Zentralitätsstufe III"
        elif self == LevelOfCentrality.IV:
            return "Zentralitätsstufe IV"
        elif self == LevelOfCentrality.Singular:
            return "Singulärer Erzeuger"
    
    def isLowerEq(self, other: 'LevelOfCentrality') -> bool:
        return self.value <= other.value
    
    def isHigherEq(self, other: 'LevelOfCentrality') -> bool:
        return self.value >= other.value
    
    @staticmethod
    def getLowerLoc(value1: 'LevelOfCentrality', value2: 'LevelOfCentrality') -> 'LevelOfCentrality':
        return LevelOfCentrality(min(value1.value, value2.value))
    
    @staticmethod
    def getUpperLoc(value1: 'LevelOfCentrality', value2: 'LevelOfCentrality') -> 'LevelOfCentrality':
        return LevelOfCentrality(max(value1.value, value2.value))
    
    def toConnectivityFunction(self) -> ConnectivityFunction:
        if self == LevelOfCentrality.II:
            return ConnectivityFunction.VFS_2
        elif self == LevelOfCentrality.III:
            return ConnectivityFunction.VFS_3
        elif self == LevelOfCentrality.IV:
            return ConnectivityFunction.VFS_4
        elif self == LevelOfCentrality.Singular:
            return ConnectivityFunction.VFS_3


