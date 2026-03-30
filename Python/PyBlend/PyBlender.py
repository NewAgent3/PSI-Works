"""
mini_blender_clone.py
A simple, single-file "Blender-like" prototype for Python 3.14

Features:
- OpenGL 3D viewport embedded in a PyQt6 window
- Orbit / pan / zoom camera controls with mouse
- Add a basic cube object
- Select object from a simple outliner and translate it with keyboard (X/Y/Z + arrows)
- Export selected object to OBJ
- Very small, educational — NOT a production-ready 3D suite

Dependencies (install with pip):
    pip install PyQt6 PyOpenGL numpy

Run:
    python mini_blender_clone.py

Notes:
- Tested conceptually; you may need proper OpenGL drivers installed.
- Intended for learning and extension.
"""

from __future__ import annotations
import sys
import math
from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *

# --------------------------- Math helpers ---------------------------


def perspective(fovy, aspect, znear, zfar):
    f = 1.0 / math.tan(math.radians(fovy) / 2.0)
    M = np.zeros((4, 4), dtype=np.float32)
    M[0, 0] = f / aspect
    M[1, 1] = f
    M[2, 2] = (zfar + znear) / (znear - zfar)
    M[2, 3] = (2 * zfar * znear) / (znear - zfar)
    M[3, 2] = -1
    return M


def look_at(eye, target, up):
    f = np.array(target) - np.array(eye)
    f = f / np.linalg.norm(f)
    u = np.array(up)
    u = u / np.linalg.norm(u)
    s = np.cross(f, u)
    s = s / np.linalg.norm(s)
    u = np.cross(s, f)
    M = np.identity(4, dtype=np.float32)
    M[0, 0:3] = s
    M[1, 0:3] = u
    M[2, 0:3] = -f
    T = np.identity(4, dtype=np.float32)
    T[0:3, 3] = -np.array(eye)
    return M @ T


def translate_matrix(v):
    M = np.identity(4, dtype=np.float32)
    M[0:3, 3] = v[0:3]
    return M


def scale_matrix(s):
    M = np.identity(4, dtype=np.float32)
    M[0, 0] = s
    M[1, 1] = s
    M[2, 2] = s
    return M


def rotate_y(angle_deg):
    a = math.radians(angle_deg)
    c = math.cos(a)
    s = math.sin(a)
    M = np.identity(4, dtype=np.float32)
    M[0, 0] = c
    M[0, 2] = s
    M[2, 0] = -s
    M[2, 2] = c
    return M

# --------------------------- Scene objects ---------------------------


@dataclass
class Mesh:
    name: str
    vertices: np.ndarray  # Nx3
    faces: np.ndarray     # Mx3 indices
    position: np.ndarray = field(
        default_factory=lambda: np.zeros(3, dtype=np.float32))
    rotation_y: float = 0.0
    scale: float = 1.0

    def model_matrix(self):
        return translate_matrix(self.position) @ rotate_y(self.rotation_y) @ scale_matrix(self.scale)

    def export_obj(self, filename):
        with open(filename, 'w') as f:
            f.write(f"# Exported by mini_blender_clone - {self.name}\n")
            for v in self.vertices:
                x, y, z = v + self.position
                f.write(f"v {x} {y} {z}\n")
            for face in self.faces:
                # OBJ uses 1-based indexing
                a, b, c = face + 1
                f.write(f"f {a} {b} {c}\n")

# --------------------------- Utility: create primitives ---------------------------


def create_cube(name='Cube') -> Mesh:
    # Unit cube centered at origin
    vs = np.array([
        [-0.5, -0.5, -0.5],
        [0.5, -0.5, -0.5],
        [0.5,  0.5, -0.5],
        [-0.5,  0.5, -0.5],
        [-0.5, -0.5,  0.5],
        [0.5, -0.5,  0.5],
        [0.5,  0.5,  0.5],
        [-0.5,  0.5,  0.5],
    ], dtype=np.float32)
    faces = np.array([
        [0, 1, 2], [0, 2, 3],
        [4, 6, 5], [4, 7, 6],
        [0, 4, 5], [0, 5, 1],
        [1, 5, 6], [1, 6, 2],
        [2, 6, 7], [2, 7, 3],
        [3, 7, 4], [3, 4, 0],
    ], dtype=np.int32)
    return Mesh(name=name, vertices=vs, faces=faces)

# --------------------------- OpenGL Widget ---------------------------


class Viewport(QOpenGLWidget):
    def __init__(self, parent=None, scene=None):
        super().__init__(parent)
        self.scene = scene
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        # camera spherical coords
        self.distance = 5.0
        self.azimuth = 45.0
        self.elevation = 25.0
        self.pan = np.array([0.0, 0.0], dtype=np.float32)
        self.last_pos = None
        self.dragging = False

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.12, 0.12, 0.12, 1.0)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, max(1, h))
        self.proj = perspective(60.0, w / max(1.0, h), 0.1, 100.0)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # build camera
        eye = self.camera_eye()
        view = look_at(eye, np.array(
            [0.0, 0.0, 0.0]) + np.array([self.pan[0], self.pan[1], 0.0]), np.array([0.0, 1.0, 0.0]))
        vp = self.proj @ view

        # simple shader-less rendering using immediate mode for clarity
        for i, obj in enumerate(self.scene.objects):
            model = obj.model_matrix()
            mvp = vp @ model
            glPushMatrix()
            glMultMatrixf(mvp.T)
            # draw wireframe
            if i == self.scene.selected_index:
                glColor3f(1.0, 0.9, 0.0)
                glLineWidth(2.0)
            else:
                glColor3f(0.7, 0.7, 0.7)
                glLineWidth(1.0)
            glBegin(GL_LINES)
            for face in obj.faces:
                for j in range(3):
                    a = obj.vertices[face[j]]
                    b = obj.vertices[face[(j+1) % 3]]
                    glVertex3f(a[0], a[1], a[2])
                    glVertex3f(b[0], b[1], b[2])
            glEnd()
            glPopMatrix()

        # ground grid
        self.draw_grid(vp)

    def draw_grid(self, vp):
        glPushMatrix()
        glMultMatrixf(vp.T)
        glColor3f(0.3, 0.3, 0.3)
        glBegin(GL_LINES)
        s = 10
        for i in range(-s, s+1):
            glVertex3f(i, 0, -s)
            glVertex3f(i, 0, s)
            glVertex3f(-s, 0, i)
            glVertex3f(s, 0, i)
        glEnd()
        glPopMatrix()

    def camera_eye(self):
        az = math.radians(self.azimuth)
        el = math.radians(self.elevation)
        x = self.distance * math.cos(el) * math.cos(az) + self.pan[0]
        y = self.distance * math.sin(el) + self.pan[1]
        z = self.distance * math.cos(el) * math.sin(az)
        return np.array([x, y, z], dtype=np.float32)

    # ---------------- mouse interaction ----------------
    def mousePressEvent(self, ev: QtGui.QMouseEvent):
        self.last_pos = ev.position()
        self.dragging = True

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent):
        if not self.dragging:
            return
        pos = ev.position()
        dx = pos.x() - self.last_pos.x()
        dy = pos.y() - self.last_pos.y()
        buttons = ev.buttons()
        if buttons & QtCore.Qt.MouseButton.LeftButton:
            # orbit
            self.azimuth += dx * 0.5
            self.elevation += dy * 0.5
            self.elevation = max(-89.9, min(89.9, self.elevation))
        elif buttons & QtCore.Qt.MouseButton.MiddleButton or (buttons & QtCore.Qt.MouseButton.LeftButton and ev.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
            # pan
            self.pan[0] += dx * 0.01
            self.pan[1] -= dy * 0.01
        self.last_pos = pos
        self.update()

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent):
        self.dragging = False

    def wheelEvent(self, ev: QtGui.QWheelEvent):
        delta = ev.angleDelta().y() / 120.0
        self.distance *= 0.9 ** delta
        self.distance = max(0.1, min(100.0, self.distance))
        self.update()

# --------------------------- Scene ---------------------------


@dataclass
class Scene:
    objects: List[Mesh] = field(default_factory=list)
    selected_index: int = 0

    def add(self, mesh: Mesh):
        self.objects.append(mesh)
        self.selected_index = len(self.objects) - 1

    def selected(self) -> Mesh | None:
        if 0 <= self.selected_index < len(self.objects):
            return self.objects[self.selected_index]
        return None

# --------------------------- Main Window + UI ---------------------------


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Mini Blender Clone — Python 3.14')
        self.resize(1100, 700)

        self.scene = Scene()
        self.scene.add(create_cube('Cube'))

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        hbox = QtWidgets.QHBoxLayout(central)

        self.viewport = Viewport(scene=self.scene)
        hbox.addWidget(self.viewport, stretch=1)

        # right panel
        panel = QtWidgets.QWidget()
        panel.setFixedWidth(300)
        pv = QtWidgets.QVBoxLayout(panel)
        pv.setContentsMargins(8, 8, 8, 8)

        # Outliner
        pv.addWidget(QtWidgets.QLabel('<b>Outliner</b>'))
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.itemSelectionChanged.connect(
            self.on_selection_changed)
        pv.addWidget(self.list_widget)

        # Buttons
        add_cube_btn = QtWidgets.QPushButton('Add Cube')
        add_cube_btn.clicked.connect(self.on_add_cube)
        pv.addWidget(add_cube_btn)

        export_btn = QtWidgets.QPushButton('Export Selected to OBJ')
        export_btn.clicked.connect(self.on_export)
        pv.addWidget(export_btn)

        pv.addWidget(QtWidgets.QLabel('<b>Shortcuts</b>'))
        pv.addWidget(QtWidgets.QLabel('Select: click in Outliner'))
        pv.addWidget(QtWidgets.QLabel(
            'Move selected: X/Y/Z then ArrowUp/ArrowDown'))
        pv.addWidget(QtWidgets.QLabel(
            'Orbit: Left drag. Pan: Middle drag or Ctrl+Left drag. Zoom: Mouse wheel'))

        pv.addStretch(1)
        hbox.addWidget(panel)

        self.update_outliner()

    def update_outliner(self):
        self.list_widget.clear()
        for obj in self.scene.objects:
            self.list_widget.addItem(obj.name)
        if 0 <= self.scene.selected_index < self.list_widget.count():
            self.list_widget.setCurrentRow(self.scene.selected_index)
        self.viewport.update()

    def on_add_cube(self):
        c = create_cube(f'Cube{len(self.scene.objects)}')
        c.position = np.array(
            [len(self.scene.objects), 0.0, 0.0], dtype=np.float32)
        self.scene.add(c)
        self.update_outliner()

    def on_export(self):
        sel = self.scene.selected()
        if not sel:
            QtWidgets.QMessageBox.warning(self, 'Export', 'No object selected')
            return
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Export OBJ', f'{sel.name}.obj', 'OBJ Files (*.obj)')
        if filename:
            sel.export_obj(filename)
            QtWidgets.QMessageBox.information(
                self, 'Export', f'Exported to {filename}')

    def on_selection_changed(self):
        r = self.list_widget.currentRow()
        if r >= 0:
            self.scene.selected_index = r
            self.viewport.update()

    def keyPressEvent(self, ev: QtGui.QKeyEvent):
        key = ev.key()
        modifiers = ev.modifiers()
        sel = self.scene.selected()
        if sel is None:
            return
        # Move mode: Press X/Y/Z to set axis, then arrows to move
        # We'll keep a simple state in window object
        if not hasattr(self, '_move_axis'):
            self._move_axis = 'X'
        if key == QtCore.Qt.Key.Key_X:
            self._move_axis = 'X'
            self.statusBar().showMessage('Move axis set to X')
        elif key == QtCore.Qt.Key.Key_Y:
            self._move_axis = 'Y'
            self.statusBar().showMessage('Move axis set to Y')
        elif key == QtCore.Qt.Key.Key_Z:
            self._move_axis = 'Z'
            self.statusBar().showMessage('Move axis set to Z')
        elif key == QtCore.Qt.Key.Key_Up:
            if self._move_axis == 'X':
                sel.position[0] += 0.1
            elif self._move_axis == 'Y':
                sel.position[1] += 0.1
            else:
                sel.position[2] += 0.1
            self.viewport.update()
            self.update_outliner()
        elif key == QtCore.Qt.Key.Key_Down:
            if self._move_axis == 'X':
                sel.position[0] -= 0.1
            elif self._move_axis == 'Y':
                sel.position[1] -= 0.1
            else:
                sel.position[2] -= 0.1
            self.viewport.update()
            self.update_outliner()
        elif key == QtCore.Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(ev)

# --------------------------- Entrypoint ---------------------------


def main():
    app = QtWidgets.QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
