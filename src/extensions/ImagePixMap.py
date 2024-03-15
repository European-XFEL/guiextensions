#############################################################################
# Created on Jan 2024
# Copyright (C) European XFEL GmbH Hamburg. All rights reserved.
#############################################################################
from qtpy.QtCore import QRectF, Qt
from qtpy.QtGui import QBrush, QColor
from qtpy.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView


class KaraboImagePixMap(QGraphicsView):

    def __init__(self, parent=None):
        """
        Initialize the KaraboImagePixMap.

        Args:
        - parent: Parent widget.
        """
        super().__init__(parent)
        self.view_rect = None
        self.start_pos = None
        self.end_pos = None
        self.temp_zoom_rect = None
        self.zoom_image = None
        self.scene_zoomed_region = None
        self.pixmap = None
        self.mouseMode = None
        self.zoom = False

        # Create a QGraphicsScene and set it to the view
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Create a QGraphicsPixmapItem and add it to the scene
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        self.view_rect = self.scene.sceneRect()

    def zoom_out(self):
        # Set the pixmap of the QGraphicsPixmapItem
        # to the original pixmap
        self.pixmap_item.setPixmap(self.pixmap_item.pixmap())
        pixmap_rect = self.pixmap_item.pixmap().rect()
        pixmap_rect_f = QRectF(pixmap_rect)
        self.scene.setSceneRect(pixmap_rect_f)

        # Fit the view to the scene's bounding rectangle
        self.fitInView(self.scene.sceneRect())

    def zoom_in(self, zoom_region):
        # Convert the rect to scene coordinates
        self.scene_zoomed_region = QRectF(
            self.mapToScene(zoom_region.topLeft()),
            self.mapToScene(zoom_region.bottomRight()))
        # Set the scene rectangle to match the zoomed region
        self.scene.setSceneRect(self.scene_zoomed_region)

        # Set the pixmap item to display the cropped pixmap
        self.pixmap_item.setPixmap(self.pixmap_item.pixmap())
        self.fitInView(self.scene.sceneRect())
        self.start_pos = self.end_pos

    def move_in(self, rect_scene, offset_x=0, offset_y=0):
        rect_scene.translate(-offset_x, -offset_y)
        scene_rect = self.scene.sceneRect()
        self.scene.setSceneRect(rect_scene)
        rect_scene_intersection = rect_scene.intersected(scene_rect)
        self.pixmap = self.pixmap_item.pixmap().copy(
            rect_scene_intersection.toRect())

    def mousePressEvent(self, event):
        """
        Handle mouse move events.

        Notes:
            - If in 'Zoom' mode and zoom enabled:
                - Draws the final yellow rectangle to
                  indicate the area to zoom.
            - If in 'Move' mode:
                - Tracks the mouse position upon clicking.
            - Otherwise, zooms out.
        """
        if self.mouseMode == "Zoom":
            if event.button() == Qt.LeftButton:
                self.start_pos = event.pos()
                brush_color = QColor(Qt.yellow)
                brush_color.setAlphaF(0.25)

                # Create the brush with the specified color
                brush = QBrush(brush_color)

                self.temp_zoom_rect = self.scene.addRect(
                    0, 0, 0, 0, pen=Qt.yellow, brush=brush)
                self.zoom = True
        elif self.mouseMode == "Move":
            self.start_pos = event.pos()

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events.

        Notes:
            - If in 'Zoom' mode and zoom enabled:
                - Draws a yellow rectangle representing the area to zoom.
            - If in 'Move' mode:
                - Moves the zoomed image if zoomed out or left button pressed.
            - Otherwise, zooms out.
        """
        if (self.mouseMode == "Zoom" and self.zoom):
            end_pos = event.pos()
            start_point_scene = self.mapToScene(self.start_pos)
            end_point_scene = self.mapToScene(end_pos)

            self.zoom_image = QRectF(
                start_point_scene, end_point_scene).normalized()

            self.temp_zoom_rect.setRect(self.zoom_image)

        if self.mouseMode == "Move":
            offset = event.pos() - self.start_pos
            self.zoom_image.translate(offset)
            self.end_pos = event.pos()
            self.move_in(self.scene_zoomed_region,
                         offset.x() / 200, offset.y() / 200)

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release event.

        Args:
        - event: QMouseEvent object representing the mouse release event.
        """
        if self.mouseMode == "Zoom":
            if event.button() == Qt.LeftButton:
                rect_in_scene = self.zoom_image.intersected(self.view_rect)
                zoom_region = self.mapFromScene(
                    rect_in_scene).boundingRect()
                self.zoom_in(zoom_region)

                if self.temp_zoom_rect:
                    self.scene.removeItem(self.temp_zoom_rect)
                    self.temp_zoom_rect = None
                    self.start_pos = None
            elif event.button() == Qt.RightButton:
                self.zoom_out()

            self.zoom = False

        elif self.mouseMode == "Move":
            if event.button() == Qt.RightButton:
                self.zoom_out()
