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
    II = 20
    III = 30
    IV = 40
    Singular = 22
    Surrounding = 21

    @staticmethod
    def defaults() -> List['LevelOfCentrality']:
        return [LevelOfCentrality.II, LevelOfCentrality.III, LevelOfCentrality.IV, LevelOfCentrality.Singular, LevelOfCentrality.Surrounding]

    @staticmethod
    def fromStr(value: str) -> 'LevelOfCentrality':
        value = value.lower()
        if value == "zentralitätsstufe ii" or value == "z ii":
            return LevelOfCentrality.II
        elif value == "zentralitätsstufe iii" or value == "z iii":
            return LevelOfCentrality.III
        elif value == "zentralitätsstufe iv" or value == "z iv":
            return LevelOfCentrality.IV
        elif value == "singulärer erzeuger" or value == "s":
            return LevelOfCentrality.Singular
        elif value == "überörtlich" or value == "ü":
            return LevelOfCentrality.Surrounding
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
        elif self == LevelOfCentrality.Surrounding:
            return "Überörtlich"
    
    def asStrShort(self) -> str:
        if self == LevelOfCentrality.II:
            return "Z II"
        elif self == LevelOfCentrality.III:
            return "Z III"
        elif self == LevelOfCentrality.IV:
            return "Z IV"
        elif self == LevelOfCentrality.Singular:
            return "S"
        elif self == LevelOfCentrality.Surrounding:
            return "Ü"

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
        elif self == LevelOfCentrality.Surrounding:
            return ConnectivityFunction.VFS_3


class NetworkSource(Enum):
    UNKNOWN = 0
    ATKIS = 1
    OSM = 2

    def fromAttributeList(attributes: List[str]) -> 'NetworkSource':
        if "objektart" in attributes and "klasse" in attributes and "kennung" in attributes:
            return NetworkSource.ATKIS
        if "osm_id" in attributes and "highway" in attributes:
            return NetworkSource.OSM
        else:
            return NetworkSource.UNKNOWN
    
    def getFilterStr(self) -> str:
        if self == NetworkSource.ATKIS:
            return "objektart in ('Fahrbahnachse', 'Fahrwegachse', 'Strassenachse', 'Strassenverkehrsanlage', 'WegPfadSteig') AND klasse not in ('Bundesautobahn', '(Kletter-)Steig im Gebirge')"
        elif self == NetworkSource.OSM:
            return "highway not in ('trunk_link ', 'trunk', 'motorway_link', 'motorway', 'raceway', 'via_ferrata', 'proposed', 'construction')  AND psv IS NULL"
        else:
            return ""

    def asStr(self) -> str:
        if self == NetworkSource.ATKIS:
            return "ATKIS"
        elif self == NetworkSource.OSM:
            return "Openstreetmap"
        else:
            return "UNKNOWN"