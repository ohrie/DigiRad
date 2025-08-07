# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LayerManager
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
from typing import Type, Optional, Tuple

import os

from PyQt5.QtCore import QTimer

from qgis.core import (
    QgsMessageLog,
    QgsProject,
    QgsCoordinateReferenceSystem,
    QgsLayerTreeGroup,
    QgsPointXY,
    QgsVectorFileWriter
)

from ..constants import CRS_STR
from ..dialogstate import DialogStateContext
from .layers.layer import DigiRadLayer
from .layers.baseLayer import BaseLayer

class LayerManager:
    def __init__(self, projectName: str, showBaseMap: bool = True):
        self._crs = QgsCoordinateReferenceSystem(CRS_STR)
        QgsProject.instance().setCrs(self._crs)

        self.iface = None
        self.projectName = projectName
        self.showBaseMap = showBaseMap

        if showBaseMap:
            self.baseLayer = BaseLayer.create()
        else:
            self.baseLayer = None

        self.layers = {}
        self.contextRef = None
        self.center = None
    
    def setContextRef(self, contextRef: DialogStateContext):
        self.contextRef = contextRef
    
    def removeAll(self):
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(self.projectName)
        if not group:
            return
        root.removeChildNode(group)
        self.layers = {}
        if self.showBaseMap:
            self.baseLayer = BaseLayer.create()
        else:
            self.baseLayer = None
    
    def show(self, center: Optional[QgsPointXY] = None):
        # If no layer is on the map, QGIS updates the CRS and extent
        # based on the first added layer.
        # As we already set the crs and extent in the location view
        # these settings are overwritten when the base map is added.
        # So we have to reset the crs and extent
        self.center = center
        project = QgsProject.instance()
        canvas = self.iface.mapCanvas()

        canvas.freeze(True)
        project.setCrs(self._crs)
        canvas.setDestinationCrs(self._crs)

        self._ensureLayer(self.baseLayer)
        canvas.freeze(False)

        # See https://gis.stackexchange.com/questions/303704/project-crs-not-being-respected-by-qgis/303710#303710
        QTimer.singleShot(20, self._setProjectCrsAndCenter)

        self.update()
    
    def _setProjectCrsAndCenter(self):
        QgsProject.instance().setCrs(self._crs)
        canvas = self.iface.mapCanvas()
        canvas.freeze(True)
        canvas.setDestinationCrs(self._crs)
        canvas.zoomScale(150000)
        if self.center:
            canvas.setCenter(self.center)
        
        canvas.freeze(False)
    
    def saveProjectToDisk(self, directory: str) -> Tuple[bool, str]:
        # Get all layers
        layers = []
        for value in self.contextRef.values():
            if isinstance(value, DigiRadLayer):
                layers.append(value)
        
        if not layers:
            return (True, "No layers")
        try:
            projectFilePath = os.path.join(directory, self.projectName + ".qgz")
            gpkgFilePath = os.path.join(directory, self.projectName + ".gpkg")
            
            # Prepare directory
            os.makedirs(directory, exist_ok=True)
            if os.path.exists(projectFilePath):
                os.remove(projectFilePath)
            if os.path.exists(gpkgFilePath):
                os.remove(gpkgFilePath)
            
            # Save layers to geopackage file
            for layer in layers:
                layerName = layer.name()
                if not layerName:
                    continue
                layerName = LayerManager._sanitizeLayername(layerName)

                options = QgsVectorFileWriter.SaveVectorOptions()
                options.driverName = "GPKG"
                options.layerName = layerName
                
                # Check if this is the first layer (create new file) or append to existing
                if os.path.exists(gpkgFilePath):
                    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
                else:
                    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
                
                error = QgsVectorFileWriter.writeAsVectorFormatV3(
                    layer.qgsLayer(),
                    gpkgFilePath,
                    layer.qgsLayer().transformContext(),
                    options
                )
                if error[0] == QgsVectorFileWriter.NoError:
                    pass
                else:
                    msg = f"Error writing layer {layer.name()}: {error[1]}"
                    QgsMessageLog.logMessage(msg)
                    return (False, msg)
                
                # Replace source in existing layer
                newSource = f"{gpkgFilePath}|layername={layerName}"
                layer.qgsLayer().setDataSource(newSource, layer.name(), "ogr")
                if layer.qgsLayer().isValid():
                    layer.qgsLayer().triggerRepaint()
                    layer.qgsLayer().reload()
                else:
                    msg = f"Error while setting data source for layer {layer.name()}: {layer.qgsLayer().error()}"
                    QgsMessageLog.logMessage(msg)
                    return (False, msg)
            
            # Save project
            success = QgsProject.instance().write(projectFilePath)
            if not success:
                msg = f"Error while saving project instance to {projectFilePath}"
                QgsMessageLog.logMessage(msg)
                return (False, msg)
            else:
                return (True, "")
        except Exception as e:
            return (False, f"Error while saving to disk: {e}")
            

    @staticmethod
    def _sanitizeLayername(layerName: str) -> str:
        layerName = layerName.replace(' ', '_').replace('-', '_')
        return ''.join(c for c in layerName if c.isalnum() or c == '_')

    def update(self):
        if not self.contextRef:
            return
        
        updatedLayers = set()
        for value in self.contextRef.values():
            if isinstance(value, DigiRadLayer):
                self.updateLayer(value)
                updatedLayers.add(value.name())
        
        layersToRemove = []
        for (layerId, layer) in self.layers.items():
            if layer.name() not in updatedLayers:
                self._removeLayer(layer)
                layersToRemove.append(layerId)
        
        for layerId in layersToRemove:
            del self.layers[layerId]
    
    def _getGroup(self, layer: Optional[DigiRadLayer] = None):
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(self.projectName)
        if not group:
            group = root.addGroup(self.projectName)
        
        if layer and layer.groupName:
            subgroup = group.findGroup(layer.groupName)
            if subgroup:
                group = subgroup
            else:
                subgroup = group.addGroup(layer.groupName)
                group = self._moveGroupToTop(group, layer.groupName)

        return (root, group)
    
    def _ensureLayer(self, layer: DigiRadLayer):
        if layer and layer.isQgsLayerPresent():
            (root, group) = self._getGroup(layer)
            qgsLayer = layer.qgsLayer()
            layerNode = group.findLayer(qgsLayer)
            if not layerNode:
                # Add the layer via the `addMapLayer` fn to the root
                # and then move it to the group 
                QgsProject.instance().addMapLayer(qgsLayer)
                layerNode = root.findLayer(qgsLayer.id())
                clone = layerNode.clone()
                group.insertChildNode(0, clone)
                layerNode.parent().removeChildNode(layerNode)
                if clone:
                    clone.setItemVisibilityChecked(layer.visible)
                    clone.setExpanded(layer.expanded)

    def _removeLayer(self, layer: DigiRadLayer):
        if layer and layer.isQgsLayerPresent():
            (root, group) = self._getGroup(layer)
            if group.findLayer(layer.qgsLayer()):
                group.removeLayer(layer.qgsLayer())
    
    def _moveToTop(self, layer: DigiRadLayer):
        if layer and layer.isQgsLayerPresent():
            (root, group) = self._getGroup(layer)
            layerNode = group.findLayer(layer.id())

            clonedNode = layerNode.clone()
            parent = layerNode.parent()
            parent.removeChildNode(layerNode)
            group.insertChildNode(0, clonedNode)
        
    def _moveGroupToTop(self, group: QgsLayerTreeGroup, childGroupName: str):
        subGroupNode = group.findGroup(childGroupName)

        clonedNode = subGroupNode.clone()
        group.removeChildNode(subGroupNode)
        group.insertChildNode(0, clonedNode)
        return group.findGroup(childGroupName)

    def updateLayer(self, layer: DigiRadLayer):
        layerName = layer.name()

        if layerName in self.layers:
            originalLayer = self.layers[layerName]
            if originalLayer.isQgsLayerPresent():
                if originalLayer.id() != layer.id():
                    self._removeLayer(originalLayer)
                    self.layers[layerName] = layer
            else:
                self.layers[layerName] = layer
        else:
            self.layers[layerName] = layer

        self._ensureLayer(layer)
        self.iface.layerTreeView().refreshLayerSymbology(layer.id())
    
    def getLayer(self, layerType: Type) -> Optional[DigiRadLayer]:
        for layer in self.layers:
            if isinstance(layer, layerType):
                return layer
        
        return None

    def updateProjectName(self, newName: str):
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(self.projectName)
        if group:
            group.setName(newName)

        self.projectName = newName

    def crs(self):
        return self._crs