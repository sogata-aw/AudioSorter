from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QTreeWidget, QListWidget, QHeaderView, QPushButton, QHBoxLayout, QLabel, QWidget, \
    QVBoxLayout, QSizePolicy
from tinytag import TinyTag


class DropLabel(QLabel):
    fileDropped = pyqtSignal(str)
    def __init__(self, text="Dépose des fichiers ici", parent=None):
        super().__init__(parent=parent)
        self.setAcceptDrops(True)
        self.setText(text)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(150)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #555;
                padding: 20px;
            }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile() and url.toLocalFile().lower().endswith((".mp3", ".flac", ".wav")):
                self.fileDropped.emit(url.toLocalFile())

class Tableau(QTreeWidget):
    fileDropped = pyqtSignal(str)
    def __init__(self, files: list[TinyTag], parent=None):
        super().__init__(parent=parent)
        self.on_change = None
        self.setAcceptDrops(True)

        self.files: list[TinyTag] = files

        self.setColumnCount(4)
        self.setHeaderLabels(["Nom", "Artiste", "Album", "Chemin d'accès"])
        self.setSelectionMode(QListWidget.ExtendedSelection)

        self.header().setStretchLastSection(True)
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.header().setSectionResizeMode(2, QHeaderView.Stretch)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
        QTreeWidget {
            background-color: #121212;
            alternate-background-color: #1A1A1A;
        }

        QHeaderView::section {
            background-color: #1E1E1E;
            color: #E0E0E0;
            padding: 6px;
            border: 1px solid #333;
            font-weight: bold;
        }

        QHeaderView::section:hover {
            background-color: #2A2A2A;
        }

        QTreeWidget::item:selected {
            background-color: #3A3A3A;
        }
        """)


        btn_remove = QPushButton("Supprimer")
        btn_remove.clicked.connect(self.remove_items)

        btn_clear = QPushButton("Tout supprimer")
        btn_clear.clicked.connect(self.clear_items)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_remove)
        btn_layout.addWidget(btn_clear)

        self.view = QWidget()
        right_layout = QVBoxLayout(self.view)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(5)
        right_layout.addLayout(btn_layout)
        right_layout.addWidget(self)
        self.view.setVisible(False)

    def remove_items(self):
        selected_items = self.selectedItems()
        items_to_remove = []
        if not selected_items:
            return
        for i in range(len(selected_items)):
            items_to_remove.append(next((j for j, x in enumerate(self.files) if x.filename == selected_items[i].text(3)), None))
            self.takeTopLevelItem(self.indexOfTopLevelItem(selected_items[i]))
        for i in reversed(items_to_remove):
            self.files.pop(i)
        if self.on_change:
            self.on_change()

    def clear_items(self):
        self.files.clear()
        self.clear()
        if self.on_change:
            self.on_change()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile() and url.toLocalFile().lower().endswith((".mp3", ".flac", ".wav")):
                self.fileDropped.emit(url.toLocalFile())


