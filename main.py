import os
import shutil
import sys
import re

from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, \
    QSizePolicy, QTreeWidgetItem, QComboBox
from tinytag import TinyTag

from errors import ErrorDialog
from tableau import DropLabel, Tableau
from utilities import *

class Fenetre(QWidget):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("Soga", "AudioSorter")
        self.solo = self.settings.value("Solo",  0,type=int)
        self.files: list[TinyTag] = []
        self.directory = ""

        self.resize(720, 480)
        self.setAcceptDrops(True)
        self.setWindowTitle("Trie d'audio")

        # --- Buttons ---
        directory_button: QPushButton = QPushButton("Choisir un dossier")
        directory_button.clicked.connect(self.open_folder_dialog)
        directory_button.setSizePolicy(
            QSizePolicy.Maximum,
            QSizePolicy.Fixed
        )

        self.launch_button_artist: QPushButton = QPushButton("Trier par artiste")
        self.launch_button_artist.clicked.connect(self.launch_trie_artiste)
        self.launch_button_artist.setEnabled(False)
        self.launch_button_artist.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        self.launch_button_album: QPushButton = QPushButton("Trier par album")
        self.launch_button_album.clicked.connect(self.launch_trie_album)
        self.launch_button_album.setEnabled(False)
        self.launch_button_album.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        # Options de tri
        self.options = QComboBox()
        self.options.addItem("Tout les artistes")
        self.options.addItem("Le premier artiste")
        if self.solo:
            self.options.setCurrentIndex(self.solo)
        self.options.currentIndexChanged.connect(self.option_changed)

        # Status
        self.status_label = QLabel("Statut : en attente")
        self.status_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #AAAAAA;
                font-style: italic;
            }
        """)
        self.status_label.setSizePolicy(
            QSizePolicy.Maximum,
            QSizePolicy.Fixed
        )

        self.footer_layout = QHBoxLayout()
        self.footer_layout.addWidget(self.launch_button_artist)
        self.footer_layout.addWidget(self.launch_button_album)
        self.footer_layout.addWidget(self.status_label)

        # --- Widgets ---
        self.directory_label = QLabel("Aucun dossier sélectionné")
        self.directory_label.setWordWrap(True)
        self.directory_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        # DropLabel
        self.drop_label = DropLabel(parent=self)
        self.drop_label.fileDropped.connect(self.add_file)

        self.file_list = Tableau(files=self.files, parent=self)
        self.file_list.on_change = self.update_views_visibility
        self.file_list.fileDropped.connect(self.add_file)

        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.directory_label)
        folder_layout.addWidget(directory_button)
        folder_layout.addWidget(QLabel("Options de trie par artiste : "))
        folder_layout.addWidget(self.options)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addLayout(folder_layout)
        self.main_layout.addWidget(self.drop_label)
        self.main_layout.addWidget(self.file_list.view)
        self.main_layout.addLayout(self.footer_layout)

    def open_folder_dialog(self):
        self.directory = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier",
                                                          self.settings.value("last_directory", "", type=str),
                                                          QFileDialog.ShowDirsOnly)
        if self.directory:
            self.directory_label.setText(self.directory)
            self.update_launch_button_state()
            self.settings.setValue("last_directory", self.directory + "/..")
            return
        self.directory_label.setText("Aucun dossier sélectionné")

    def add_file(self, path):
        if path not in self.files:
            tags = TinyTag.get(path)
            if tags and not next(filter(lambda x: x.filename == path, self.files), None):
                self.files.append(tags)
                item = QTreeWidgetItem([tags.title, tags.artist, tags.album, tags.filename])
                self.file_list.addTopLevelItem(item)
        self.update_launch_button_state()
        self.update_views_visibility()

    def launch_trie_artiste(self):
        self.set_status("En cours de traitement", "working")
        errors = []
        for file in self.files:
            artist = file.artist
            if self.solo == 1:
                print("I'm getting here")
                artist = get_main_artist(artist)
            try:
                if not os.path.exists(self.directory + "/" + valid_filename(artist)):
                    os.mkdir(self.directory + "/" + valid_filename(artist))
                if not os.path.exists(self.directory + "/" + valid_filename(artist) + "/" + file.filename):
                    shutil.move(file.filename, self.directory + "/" + valid_filename(artist) + "/")
                else:
                    errors.append(
                        f"Il existe déjà un fichier du même nom dans le dossier de destination pour {file.filename}")
            except FileNotFoundError:
                if not os.path.exists(self.directory + "/" + valid_filename(artist) + "/" + file.filename):
                    errors.append(f"Le fichier suivant n'existe pas : {file.filename}")
            except shutil.Error:
                errors.append(
                    f"Il existe déjà un fichier du même nom dans le dossier de destination pour {file.filename}")
            except PermissionError:
                errors.append(f"Permission non accordé ! Impossible de déplacer le fichier {file.filename}")

        if errors:
            self.set_status(f"Terminé avec {len(errors)} erreurs", "errors")
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
            self.set_status("Terminé sans erreur", "done")
            self.file_list.clear()
            self.files.clear()
            self.update_views_visibility()

    def launch_trie_album(self):
        self.set_status("En cours de traitement", "working")
        errors = []
        for file in self.files:
            album = file.album
            try:
                if not os.path.exists(self.directory + "/" + valid_filename(album)):
                    os.mkdir(self.directory + "/" + valid_filename(album))
                if not os.path.exists(self.directory + "/" + valid_filename(album) + "/" + file.filename):
                    shutil.move(file.filename, self.directory + "/" + valid_filename(album) + "/")
                else:
                    errors.append(
                        f"Il existe déjà un fichier du même nom dans le dossier de destination pour {file.filename}")
            except FileNotFoundError:
                if not os.path.exists(self.directory + "/" + valid_filename(album) + "/" + file.filename):
                    errors.append(f"Le fichier suivant n'existe pas : {file.filename}")
            except shutil.Error:
                errors.append(
                    f"Il existe déjà un fichier du même nom dans le dossier de destination pour {file.filename}")
            except PermissionError:
                errors.append(f"Permission non accordé ! Impossible de déplacer le fichier {file.filename}")

        if errors:
            self.set_status(f"Terminé avec {len(errors)} erreurs", "errors")
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
            self.set_status("Terminé sans erreur", "done")
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

    def set_status(self, text, state="idle"):
        self.status_label.setText(f"Statut : {text}")

        colors = {
            "idle": "#AAAAAA",
            "working": "#4FC3F7",
            "done": "#81C784",
            "error": "#E57373",
        }

        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.get(state, "#AAAAAA")};
                font-style: italic;
            }}
        """)

    def option_changed(self, index):
        self.settings.setValue("Solo", index)
        self.solo = index



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
