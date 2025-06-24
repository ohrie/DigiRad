# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Qt Helpers
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
from qgis.PyQt.QtWidgets import QMessageBox


class QtHelper:

    @staticmethod
    def askForLayerDeletion(parent = None) -> bool:
        reply = QMessageBox.question(
            parent,
            "Generierte Layer entfernen",  # Dialog title
            "Wenn Sie diesen Bearbeitungsschritt erneut ausführen, werden nachgelagerte Bearbeitungsschritte gelöscht. Möchten Sie fortfahren?",  # Dialog message
            QMessageBox.Yes | QMessageBox.No,  # Buttons
            QMessageBox.No  # Default button
        )
        
        return reply == QMessageBox.Yes