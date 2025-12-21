import sys

import tinytag.tinytag
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, \
    QSizePolicy, QTreeWidgetItem, QComboBox

from errors import ErrorDialog
from tableau import DropLabel, Tableau
from utilities import *
from widgets.status import Status


class Fenetre(QWidget):
    def __init__(self):
        super().__init__()

        self.q_settings = QSettings("Soga", "AudioSorter")
        self.settings = self.q_settings.value("Solo", 0, type=int)
        self.files: list[TinyTag] = []
        self.directory = ""

        self.resize(720, 480)
        self.setAcceptDrops(True)
        self.setWindowTitle("Trie d'audio")

        # --- Sélecteur de dossier ---
        self.directory_label = QLabel("Aucun dossier sélectionné")
        self.directory_label.setWordWrap(True)
        self.directory_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        directory_button: QPushButton = QPushButton("Choisir un dossier")
        directory_button.clicked.connect(self.open_folder_dialog)
        directory_button.setSizePolicy(
            QSizePolicy.Maximum,
            QSizePolicy.Fixed
        )

        # --- Boutons de tri ---

        self.launch_button_artist: QPushButton = QPushButton("Trier par artiste")
        self.launch_button_artist.clicked.connect(self.trier_par_artiste)
        self.launch_button_artist.setEnabled(False)
        self.launch_button_artist.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        self.launch_button_album: QPushButton = QPushButton("Trier par album")
        self.launch_button_album.clicked.connect(self.trier_par_album)
        self.launch_button_album.setEnabled(False)
        self.launch_button_album.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        # --- Options de tri ---
        self.options = QComboBox()
        self.options.addItem("Tout les artistes")
        self.options.addItem("Le premier artiste")
        if self.settings:
            self.options.setCurrentIndex(self.settings)
        self.options.currentIndexChanged.connect(self.option_changed)

        # --- Status ---
        self.status_label = Status()

        # --- DropLabel ---
        self.drop_label = DropLabel(parent=self)
        self.drop_label.fileDropped.connect(self.add_file)

        # --- Liste des fichiers ---
        self.file_list = Tableau(files=self.files, parent=self)
        self.file_list.on_change = self.update_views_visibility
        self.file_list.fileDropped.connect(self.add_file)

        # --- Header Layout ---
        header_layout = QHBoxLayout()
        header_layout.addWidget(self.directory_label)
        header_layout.addWidget(directory_button)
        header_layout.addWidget(QLabel("Options de trie par artiste : "))
        header_layout.addWidget(self.options)

        # --- Footer Layout ---
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(self.launch_button_artist)
        footer_layout.addWidget(self.launch_button_album)
        footer_layout.addWidget(self.status_label)

        # --- Main Layout ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addLayout(header_layout)
        self.main_layout.addWidget(self.drop_label)
        self.main_layout.addWidget(self.file_list.view)
        self.main_layout.addLayout(footer_layout)

    def open_folder_dialog(self):
        self.directory = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier",
                                                          self.q_settings.value("last_directory", "", type=str),
                                                          QFileDialog.ShowDirsOnly)
        if self.directory:
            self.directory_label.setText(self.directory)
            self.update_launch_button_state()
            self.q_settings.setValue("last_directory", self.directory + "/..")
            return
        self.directory_label.setText("Aucun dossier sélectionné")

    def add_file(self, path):
        if path not in self.files:
            tags: tinytag.tinytag.TinyTag = TinyTag.get(path)
            if tags and not next(filter(lambda x: x.filename == path, self.files), None):
                self.files.append(tags)
                item = QTreeWidgetItem([tags.title, tags.artist, tags.album, tags.filename])
                self.file_list.addTopLevelItem(item)
        self.update_launch_button_state()
        self.update_views_visibility()

    def trier_par_artiste(self):
        self.status_label.set_status("En cours de traitement", "working")
        errors = []
        for file in self.files:
            trie(self.directory, file, file.artist, errors)
        self.handle_errors(errors)

    def trier_par_album(self):
        self.status_label.set_status("En cours de traitement", "working")
        errors = []
        for file in self.files:
            trie(self.directory, file, file.album, errors)
        self.handle_errors(errors)

    def handle_errors(self, errors):
        if errors:
            self.status_label.set_status(f"Terminé avec {len(errors)} erreurs", "errors")
            item_to_remove = [i for i, f in enumerate(self.files) if not any(f.filename in error for error in errors)]

            for j in reversed(item_to_remove):
                self.files.pop(j)

            self.file_list.clear()

            for file in self.files:
                item = QTreeWidgetItem([file.title, file.artist, file.album, file.filename])
                self.file_list.addTopLevelItem(item)

            dialog = ErrorDialog(errors=errors, parent=self)
            dialog.exec_()
        else:
            self.status_label.set_status("Terminé sans erreur", "done")
            self.file_list.clear()
            self.files.clear()
            self.update_views_visibility()

    def update_launch_button_state(self):
        state = bool(self.files) and self.directory != ""
        self.launch_button_artist.setEnabled(state)
        self.launch_button_album.setEnabled(state)

    def update_views_visibility(self):
        has_files = bool(self.files)
        self.update_launch_button_state()
        self.drop_label.setVisible(not has_files)
        self.file_list.view.setVisible(has_files)

    def option_changed(self, index):
        self.q_settings.setValue("Solo", index)
        self.settings = index


if __name__ == '__main__':
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    app.setStyleSheet("""
    QWidget {
        background-color: #121212;
        color: #E0E0E0;
    }
    
    QPushButton {
        background-color: #1E1E1E;
        border: 1px solid #333;
        border-radius: 6px;
        padding: 6px 12px;
    }

    QPushButton:hover {
        background-color: #2A2A2A;
    }

    QPushButton:disabled{
        background-color: #858585;
    }

    QPushButton:pressed {
        background-color: #333;
    }

    QLabel {
        color: #AAAAAA;
    }""")

    root = Fenetre()
    root.showMaximized()

    sys.exit(app.exec_())
