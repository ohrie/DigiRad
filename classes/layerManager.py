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
from typing import Type, Optional

from qgis.core import (
    QgsMessageLog,
    QgsProject,
    QgsCoordinateReferenceSystem,
    QgsLayerTreeGroup
)

from ..dialogstate import DialogStateContext
from .layers.layer import DigiRadLayer
from .layers.baseLayer import BaseLayer

class LayerManager:
    def __init__(self, projectName: str, showBaseMap: bool = True):
        self._crs = QgsCoordinateReferenceSystem("EPSG:3857")
        QgsProject.instance().setCrs(self._crs)

        self.iface = None
        self.projectName = projectName

        if showBaseMap:
            self.baseLayer = BaseLayer.create()
        else:
            self.baseLayer = None

        self.layers = {}
        self.contextRef = None
    
    def setContextRef(self, contextRef: DialogStateContext):
        self.contextRef = contextRef
    
    def show(self):
        (root, group) = self._getGroup()
        
        self._ensureLayer(self.baseLayer)
        self.update()
    
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