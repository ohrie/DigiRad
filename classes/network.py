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
from typing import Self
from enum import Enum

class ConnectivityFunction(Enum):
    VFS_1 = 1
    VFS_2 = 2
    VFS_3 = 3
    VFS_4 = 4
    VFS_5 = 5

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
    OBERZENTRUM = 2
    MITTELZENTRUM = 3
    GRUNDZENTRUM = 4

    def fromStr(value: str) -> Self:
        value = value.lower()
        if "oberzent" in value:
            return LevelOfCentrality.OBERZENTRUM
        elif "mittelze" in value:
            return LevelOfCentrality.MITTELZENTRUM
        elif "grundz" in value:
            return LevelOfCentrality.GRUNDZENTRUM
        else:
            raise ValueError(f"'{value}' is not a valid level of centrality")
    
    def asStr(self) -> str:
        n = self.name.lower()
        n = n[0].upper() + n[1:]
        return n
    
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
            case LevelOfCentrality.OBERZENTRUM:
                return ConnectivityFunction.VFS_2
            case LevelOfCentrality.MITTELZENTRUM:
                return ConnectivityFunction.VFS_3
            case LevelOfCentrality.GRUNDZENTRUM:
                return ConnectivityFunction.VFS_4

    
