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

from typing import Optional
from PyQt5.QtWidgets import QFileDialog
from qgis.PyQt.QtWidgets import QMessageBox, QAbstractButton

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
    
    Yes = 1
    No = 2
    KeepOldProject = 3

    @staticmethod
    def askForProjectRestart(parent = None) -> int:
        msgBox = QMessageBox(parent=parent, icon=QMessageBox.Question)
        msgBox.setWindowTitle("Projekt neustarten")
        msgBox.setText("Wenn Sie das Projekt neustarten, werden alle schon erzeugten Daten gelöscht. Möchten Sie fortfahren?")
        msgBox.setIcon
        yesButton = msgBox.addButton("Ja", QMessageBox.YesRole)
        noButton = msgBox.addButton("Nein", QMessageBox.NoRole)
        keepOldProjectButton = msgBox.addButton("Projektdaten behalten", QMessageBox.ActionRole)

        msgBox.exec()
        if msgBox.clickedButton() == yesButton:
            return QtHelper.Yes
        if msgBox.clickedButton() == noButton:
            return QtHelper.No
        if msgBox.clickedButton() == keepOldProjectButton:
            return QtHelper.KeepOldProject

        # reply = QMessageBox.question(
        #     parent,
        #     "Projekt neustarten",  # Dialog title
        #     "Wenn Sie das Projekt neustarten, werden alle schon erzeugten Daten gelöscht. Möchten Sie fortfahren?",  # Dialog message
        #     QMessageBox.Yes | QMessageBox.No |  # Buttons
        #     QMessageBox.No  # Default button
        # )
        
        # return reply == QMessageBox.Yes
    
    @staticmethod
    def showInformationBox(parent = None, title: str = "", message: str = ""):
        QMessageBox.information(
            parent,
            title,
            message,
            QMessageBox.Ok, # Button
            QMessageBox.Ok  # Default button
        )
    
    @staticmethod
    def askForProjectToSaveDirectory(parent = None) -> Optional[str]:
        """Open folder dialog and get selected folder"""
        directoryPath = QFileDialog.getExistingDirectory(
            parent,
            "Ordner auswählen",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        return directoryPath