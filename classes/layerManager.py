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

from qgis.core import QgsMessageLog, QgsProject, QgsRasterLayer, QgsCoordinateReferenceSystem

from .layers.centerLayer import CenterLayer
from .layers.directRouteNetworkLayer import DirectRouteNetworklayer

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
    
    def _createBaseLayer(self):
        tms = "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=15&zmin=6"
        layer = QgsRasterLayer(tms, "Hintergrundkarte", "wms")
        return layer
    
    def show(self):
        (root, group) = self._getGroup()
        
        self._ensureLayer(root, group, self.baseLayer)
        self._ensureLayer(root, group, self.centerLayer)
        self._ensureLayer(root, group, self.directRouteLayer)
    
    def _getGroup(self):
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(self.projectName)
        if not group:
            group = root.addGroup(self.projectName)
        return (root, group)
    
    def _ensureLayer(self, root, group, layer):
        if layer:
            if not group.findLayer(layer.name()):
                # Add the layer via the `addMapLayer` fn to the root
                # and then move it to the group 
                QgsProject.instance().addMapLayer(layer)
                layer = root.findLayer(layer.id())
                clone = layer.clone()
                group.insertChildNode(0, clone)
                layer.parent().removeChildNode(layer)

    
    def _removeLayer(self, group, layer):
        if layer:
            if group.findLayer(layer.name()):
                group.removeLayer(layer)
    
    def _moveToTop(self, group, layer):
        layerNode = group.findLayer(layer.id())

        cloned_node = layerNode.clone()
        parent = layerNode.parent()
        parent.removeChildNode(layerNode)
        group.insertChildNode(0, cloned_node)


    def updateCenterLayer(self, centerLayer: CenterLayer):
        (root, group) = self._getGroup()

        if self.centerLayer:
            self._removeLayer(group, self.centerLayer.qgsLayer())
        
        self._ensureLayer(root, group, centerLayer.qgsLayer())
        # self._moveToTop(group, centerLayer.qgsLayer())

        self.centerLayer = centerLayer
        self.iface.layerTreeView().refreshLayerSymbology(centerLayer.qgsLayer().id())

    def updateDirectRouteLayer(self, directRouteLayer: DirectRouteNetworklayer):
        (root, group) = self._getGroup()

        if self.directRouteLayer:
            self._removeLayer(group, self.directRouteLayer.qgsLayer())
        
        self._ensureLayer(root, group, directRouteLayer.qgsLayer())
        # self._moveToTop(group, directRouteLayer.qgsLayer())

        self.directRouteLayer = directRouteLayer
        self.iface.layerTreeView().refreshLayerSymbology(directRouteLayer.qgsLayer().id())

    def updateProjectName(self, newName: str):
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(self.projectName)
        if group:
            group.setName(newName)

        self.projectName = newName

    def crs(self):
        return self._crs