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

from typing import List, Tuple
import csv
from fuzzywuzzy import fuzz

from qgis.core import QgsMessageLog, QgsPointXY

class ARSCode:
    def __init__(self, code: str, name: str, center: QgsPointXY):
        self.code = code
        self.name = name
        self.center = center

class ARSIndex:
    def __init__(self, filePath: str):
        """
        Load CSV file into ARSCode objects
        
        The CSV has headers:
        X;Y;GeografischerName_GEN;Bezeichnung;Land;ARS
        
        Where:
        - X and Y become center
        - GeografischerName_GEN becomes name
        - ARS becomes code
        """
        arsCodes = {}

        try:
            with open(filePath, 'r', encoding='utf-8') as file:
                # Use csv.reader with semicolon delimiter
                csvReader = csv.reader(file, delimiter=';')
                
                # Get header row to verify structure
                header = next(csvReader)
                
                # Verify that the required columns exist
                requiredColumns = ['X', 'Y', 'GeografischerName_GEN', 'ARS']
                for column in requiredColumns:
                    if column not in header:
                        raise ValueError(f"Required column '{column}' not found in CSV header")
                
                # Get indices for the columns we need
                xIndex = header.index('X')
                yIndex = header.index('Y')
                nameIndex = header.index('GeografischerName_GEN')
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
                        
                        # Create ARSCode object and add to list
                        arsCodes[code] = ARSCode(code=code, name=name, center=center)
                    
                    except (ValueError, IndexError) as e:
                        QgsMessageLog.logMessage(f"Error processing row {row}: {e}")
                        continue
        
        except Exception as e:
            QgsMessageLog.logMessage(f"Error reading CSV file: {e}")
        
        self.arsCodes = arsCodes
    
    def searchByName(self, searchName: str, threshold: int = 70, maxResults: int = 10) -> List[Tuple[ARSCode, int]]:
        """
        Search ARSCode entries based on name using fuzzy matching
        
        Args:
            searchName: Name to search for
            threshold: Minimum similarity score (0-100) to include in results
        
        Returns:
            List of tuples containing (ARSCode, similarity_score) sorted by score descending
        """
        # Convert search name to lowercase for better matching
        searchName = searchName.lower()
        results = []

        for arsCode in self.arsCodes.values():
            # Get similarity score using fuzzywuzzy's token sort ratio
            # This works well for names that might have words in different orders
            similarity = fuzz.token_sort_ratio(arsCode.name.lower(), searchName)

            # Only include results above the threshold
            if similarity >= threshold:
                results.append((arsCode, similarity))
        
        # Sort results by similarity score (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        limit = min(len(results), maxResults)

        return results[0:limit]
    
    def getARSCodeByName(self, name: str) -> ARSCode:
        for code in self.arsCodes.values():
            if code.name == name:
                return code
        
        return None