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
    QgsRasterLayer,
    QgsMapLayer,
    QgsCoordinateReferenceSystem
)

from ..dialogstate import DialogStateContext
from .layers.layer import DigiRadLayer

class LayerManager:
    def __init__(self, projectName: str, showBaseMap: bool = True):
        self._crs = QgsCoordinateReferenceSystem("EPSG:3857")
        QgsProject.instance().setCrs(self._crs)

        self.iface = None
        self.projectName = projectName

        if showBaseMap:
            self.baseLayer = self._createBaseLayer()
        else:
            self.baseLayer = None

        self.centerLayer = None
        self.directRouteLayer = None
        self.routeLayer = None
        self.layers = {}
        self.contextRef = None
    
    def setContextRef(self, contextRef: DialogStateContext):
        self.contextRef = contextRef
    
    def _createBaseLayer(self):
        tms = "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=15"
        layer = QgsRasterLayer(tms, "Hintergrundkarte", "wms")
        return layer
    
    def show(self):
        (root, group) = self._getGroup()
        
        self._ensureLayer(root, group, self.baseLayer)
        self._ensureLayer(root, group, self.centerLayer)
        self._ensureLayer(root, group, self.directRouteLayer)
    
    def update(self):
        if not self.contextRef:
            return
        
        updatedLayers = set()
        for value in self.contextRef.values():
            if isinstance(value, DigiRadLayer):
                self.updateLayer(value)
                updatedLayers.add(value.name())
        
        (root, group) = self._getGroup()
        for layer in self.layers.values():
            if layer.name() not in updatedLayers:
                self._removeLayer(group, layer.qgsLayer())
    
    def _getGroup(self):
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(self.projectName)
        if not group:
            group = root.addGroup(self.projectName)
        
        return (root, group)
    
    def _ensureLayer(self, root, group, layer: QgsMapLayer):
        if layer:
            if not group.findLayer(layer):
                # Add the layer via the `addMapLayer` fn to the root
                # and then move it to the group 
                QgsProject.instance().addMapLayer(layer)
                layer = root.findLayer(layer.id())
                clone = layer.clone()
                group.insertChildNode(0, clone)
                layer.parent().removeChildNode(layer)

    
    def _removeLayer(self, group, layer):
        if layer and group.findLayer(layer):
            group.removeLayer(layer)
    
    def _moveToTop(self, group, layer):
        layerNode = group.findLayer(layer.id())

        cloned_node = layerNode.clone()
        parent = layerNode.parent()
        parent.removeChildNode(layerNode)
        group.insertChildNode(0, cloned_node)

    def updateLayer(self, layer: DigiRadLayer):
        layerName = layer.name()
        (root, group) = self._getGroup()

        if layerName in self.layers:
            originalLayer = self.layers[layerName]
            if originalLayer.isQgsLayerPresent():
                if originalLayer.id() != layer.id():
                    self._removeLayer(group, originalLayer.qgsLayer())
                    self.layers[layerName] = layer
            else:
                self.layers[layerName] = layer
        else:
            self.layers[layerName] = layer

        self._ensureLayer(root, group, layer.qgsLayer())
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