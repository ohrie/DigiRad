# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ARS
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

from typing import List, Tuple, Optional
import csv

from qgis.core import QgsMessageLog, QgsPointXY

class ARSCodeStr:
    def __init__(self, code: str) -> 'ARSCodeStr':
        self.code = code
    
    @staticmethod
    def empty() -> 'ARSCodeStr':
        return ARSCodeStr("")

    @staticmethod
    def fromStr(code: str) -> Optional['ARSCodeStr']:
        if len(code) > 12:
            return None
        if not code.isnumeric():
            return None
        
        return ARSCodeStr(code.ljust(12, "0"))
    
    def isEmpty(self) -> bool:
        return self.code == ""
    
    def isZ2(self) -> bool:
        return len(self.getRelevantPart()) <= 5
    
    def getRelevantPart(self) -> str:
        if self.isEmpty():
            return ""
        
        sub = 12
        # Find the right most zero before a non zero
        for (i, c) in enumerate(reversed(self.code)):
            if c != "0":
                sub -= i
                break
        
        return self.code[0:sub]
    
    def isWithin(self, other: 'ARSCodeStr') -> bool:
        if self.isEmpty():
            return False
        
        sub = 12
        # Find the right most zero before a non zero
        for (i, c) in enumerate(reversed(other.code)):
            if c != "0":
                sub -= i
                break
        
        otherSub = other.getRelevantPart()
        
        return self.code[0:len(otherSub)] == otherSub


class ARSCode:
    def __init__(self, code: ARSCodeStr, name: str, center: QgsPointXY):
        self.code = code
        self.name = name
        self.center = center

class ARSIndex:
    def __init__(self, filePath: str):
        """
        Load CSV file into ARSCode objects
        
        The CSV has headers:
        X;Y;Name;ARS
        
        """
        arsCodes = {}
        arsNamesIndex = {}

        try:
            with open(filePath, 'r', encoding='utf-8') as file:
                # Use csv.reader with semicolon delimiter
                csvReader = csv.reader(file, delimiter=';')
                
                # Get header row to verify structure
                header = next(csvReader)
                
                # Verify that the required columns exist
                requiredColumns = ['X', 'Y', 'Name', 'ARS']
                for column in requiredColumns:
                    if column not in header:
                        raise ValueError(f"Required column '{column}' not found in CSV header")
                
                # Get indices for the columns we need
                xIndex = header.index('X')
                yIndex = header.index('Y')
                nameIndex = header.index('Name')
                codeIndex = header.index('ARS')
                
                # Process each row
                for row in csvReader:
                    # Skip empty rows
                    if not row:
                        continue
                    
                    try:
                        # Convert X and Y to float and create center point
                        center = QgsPointXY(float(row[xIndex]), float(row[yIndex]))
                        
                        # Get name and code
                        name = row[nameIndex]
                        code = row[codeIndex]

                        code = ARSCodeStr.fromStr(code)
                        
                        # Create ARSCode object and add to list
                        ars = ARSCode(code=code, name=name, center=center)
                        arsCodes[code] = ars
                        arsNamesIndex[name.lower()] = name
                    
                    except (ValueError, IndexError) as e:
                        QgsMessageLog.logMessage(f"Error processing row {row}: {e}")
                        continue
        
        except Exception as e:
            QgsMessageLog.logMessage(f"Error reading CSV file: {e}")
        
        self.arsCodes = arsCodes
        self.arsNamesIndex = arsNamesIndex
    
    def findNamesBySearchName(self, searchName: str, maxResults: int = 10) -> List[str]:
        searchName = searchName.lower().strip()
        if not searchName:
            return []
        
        results = []

        for (nameLower, name) in self.arsNamesIndex.items():
            if nameLower.startswith(searchName):
                results.append(name)
                if maxResults > 0 and len(results) > maxResults:
                    break
        
        results.sort()
        return results
    
    def searchByName(self, searchName: str, threshold: float = 0.7, maxResults: int = 10) -> List[Tuple[ARSCode, int]]:
        """
        Search ARSCode entries based on name using fuzzy matching
        
        Args:
            searchName: Name to search for
            threshold: Minimum similarity score (0-1.0) to include in results
        
        Returns:
            List of tuples containing (ARSCode, similarity_score) sorted by score descending
        """
        # Convert search name to lowercase for better matching
        searchName = searchName.lower()
        results = []

        for arsCode in self.arsCodes.values():
            similarity = self.similarity(arsCode.name.lower(), searchName)

            # Only include results above the threshold
            if similarity >= threshold:
                results.append((arsCode, similarity))
        
        # Sort results by similarity score (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        limit = min(len(results), maxResults)

        return results[0:limit]
    
    def similarity(self, name1, name2):
        """
        Calculate similarity between two names using Levenshtein distance.
        
        Args:
            name1 (str): First name (lowercase)
            name2 (str): Second name (lowercase)
        
        Returns:
            float: Similarity score between 0.0 (no similarity) and 1.0 (identical)
        """
        
        def levenshtein_distance(s1, s2):
            """Calculate Levenshtein distance between two strings."""
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            # Create a matrix to store distances
            previous_row = list(range(len(s2) + 1))
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    # Cost of insertions, deletions, and substitutions
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        # Handle empty inputs
        if not name1 and not name2:
            return 1.0
        if not name1 or not name2:
            return 0.0
        
        # Calculate Levenshtein distance
        distance = levenshtein_distance(name1, name2)
        
        # Convert distance to similarity score (0-1 scale)
        max_length = max(len(name1), len(name2))
        similarity = 1.0 - (distance / max_length) if max_length > 0 else 1.0
        
        return round(similarity, 3)
    
    def getARSCodeByName(self, name: str) -> ARSCode:
        for code in self.arsCodes.values():
            if code.name == name:
                return code
        
        return None