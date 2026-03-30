import sys
import os
import math
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QHBoxLayout
from PyQt5.QtOpenGL import QGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
import pyassimp
from PIL import Image


class GLViewport(QGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = None
        self.x_rot = 0
        self.y_rot = 0
        self.zoom = -6

    def load_fbx(self, path):
        if self.scene:
            pyassimp.release(self.scene)
        self.scene = pyassimp.load(path)
        self.update()

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        glClearColor(0.1, 0.1, 0.15, 1)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h if h != 0 else 1, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0, 0, self.zoom)
        glRotatef(self.x_rot, 1, 0, 0)
        glRotatef(self.y_rot, 0, 1, 0)

        if self.scene:
            self.draw_node(self.scene.rootnode)

    def draw_node(self, node):
        glPushMatrix()
        for mesh in node.meshes:
            glBegin(GL_TRIANGLES)
            for face in mesh.faces:
                for idx in face:
                    if len(mesh.normals) > 0:
                        glNormal3f(*mesh.normals[idx])
                    if len(mesh.vertices) > 0:
                        glVertex3f(*mesh.vertices[idx])
            glEnd()
        for child in node.children:
            self.draw_node(child)
        glPopMatrix()

    def mouseMoveEvent(self, event):
        self.y_rot += event.x() * 0.01
        self.x_rot += event.y() * 0.01
        self.update()

    def wheelEvent(self, event):
        self.zoom += event.angleDelta().y() / 240
        self.update()

    def bake_sprite(self, output_dir, angles=16, size=256):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        for i in range(angles):
            self.x_rot = 0
            self.y_rot = 360 / angles * i
            self.makeCurrent()
            glViewport(0, 0, size, size)
            self.paintGL()
            glPixelStorei(GL_PACK_ALIGNMENT, 1)
            data = glReadPixels(0, 0, size, size, GL_RGBA, GL_UNSIGNED_BYTE)
            img = Image.frombytes("RGBA", (size, size), data)
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
            img.save(os.path.join(output_dir, f"sprite_{i}.png"))


class Mini3DEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini3D Editor Prototype")
        self.setGeometry(100, 100, 900, 600)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        self.viewport = GLViewport(self)
        main_layout.addWidget(self.viewport)

        button_layout = QHBoxLayout()

        load_btn = QPushButton("Load FBX")
        load_btn.clicked.connect(self.load_fbx)
        button_layout.addWidget(load_btn)

        bake_btn = QPushButton("Bake Sprites")
        bake_btn.clicked.connect(self.bake_sprites)
        button_layout.addWidget(bake_btn)

        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(self.reset_view)
        button_layout.addWidget(reset_btn)

        main_layout.addLayout(button_layout)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def load_fbx(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select FBX File", "", "FBX Files (*.fbx)")
        if path:
            self.viewport.load_fbx(path)

    def bake_sprites(self):
        output_dir = QFileDialog.getExistingDirectory(
            self, "Select Output Folder")
        if output_dir:
            self.viewport.bake_sprite(output_dir)

    def reset_view(self):
        self.viewport.x_rot = 0
        self.viewport.y_rot = 0
        self.viewport.zoom = -6
        self.viewport.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Mini3DEditor()
    window.show()
    sys.exit(app.exec_())
