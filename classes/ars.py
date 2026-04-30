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
        if not isinstance(code, str):
            return None
        if len(code) > 12:
            return None
        if not code.isnumeric():
            return None
        
        return ARSCodeStr(code.ljust(12, "0"))
    
    def isEmpty(self) -> bool:
        return self.code == ""
    
    def isZ2(self) -> bool:
        if self.isEmpty():
            return False
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
        
        # Pad `sub` to ARS parts (L, K, RB, VG etc.).
        # E.g. when we have a VG with the value 220 then the end result would remove the
        # trailing 0
        if sub == 1:
            sub = 2
        elif sub == 4:
            sub = 5
        elif sub >= 6 and sub <= 8:
            sub = 9
        elif sub == 10 or sub == 11:
            sub = 12

        return self.code[0:sub]
    
    def isWithin(self, other: 'ARSCodeStr') -> bool:
        if self.isEmpty():
            return False
        
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