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
from typing import Self, List
from enum import Enum

class ConnectivityFunction(Enum):
    VFS_1 = 1
    VFS_2 = 2
    VFS_3 = 3
    VFS_4 = 4
    VFS_5 = 5

    @staticmethod
    def defaults() -> List[Self]:
        return [ConnectivityFunction.VFS_2, ConnectivityFunction.VFS_3, ConnectivityFunction.VFS_4]
    
    def asStr(self) -> str:
        match self:
            case ConnectivityFunction.VFS_1:
                return "VFS I"
            case ConnectivityFunction.VFS_2:
                return "VFS II"
            case ConnectivityFunction.VFS_3:
                return "VFS III"
            case ConnectivityFunction.VFS_4:
                return "VFS IV"
            case ConnectivityFunction.VFS_5:
                return "VFS V"
    
    def isLowerEq(self, other: Self) -> bool:
        return self.value <= other.value
    
    def isHigherEq(self, other: Self) -> bool:
        return self.value >= other.value

class LevelOfCentrality(Enum):
    II = 2
    III = 3
    IV = 4

    @staticmethod
    def defaults() -> List[Self]:
        return [LevelOfCentrality.II, LevelOfCentrality.III, LevelOfCentrality.IV]

    def fromStr(value: str) -> Self:
        value = value.lower()
        if "oberzent" in value or value == "zentralitätsstufe ii":
            return LevelOfCentrality.II
        elif "mittelze" in value or value == "zentralitätsstufe iii":
            return LevelOfCentrality.III
        elif "grundz" in value or value == "zentralitätsstufe iv":
            return LevelOfCentrality.IV
        else:
            raise ValueError(f"'{value}' is not a valid level of centrality")
    
    def asStr(self) -> str:
        match self:
            case LevelOfCentrality.II:
                return "Zentralitätsstufe II"
            case LevelOfCentrality.III:
                return "Zentralitätsstufe III"
            case LevelOfCentrality.IV:
                return "Zentralitätsstufe IV"
    
    def isLowerEq(self, other: Self) -> bool:
        return self.value <= other.value
    
    def isHigherEq(self, other: Self) -> bool:
        return self.value >= other.value
    
    def getLowerLoc(value1: Self, value2: Self) -> Self:
        return LevelOfCentrality(min(value1.value, value2.value))
    
    def getUpperLoc(value1: Self, value2: Self) -> Self:
        return LevelOfCentrality(max(value1.value, value2.value))
    
    def toConnectivityFunction(self) -> ConnectivityFunction:
        match self:
            case LevelOfCentrality.II:
                return ConnectivityFunction.VFS_2
            case LevelOfCentrality.III:
                return ConnectivityFunction.VFS_3
            case LevelOfCentrality.IV:
                return ConnectivityFunction.VFS_4

    
