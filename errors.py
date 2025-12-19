from PyQt5.QtWidgets import QListWidget, QPushButton, QLabel, QVBoxLayout, QDialog


class ErrorDialog(QDialog):
    def __init__(self, errors: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Erreurs rencontrées")
        self.resize(500, 300)

        layout = QVBoxLayout(self)

        title = QLabel(f"{len(errors)} erreur(s) détectée(s)")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)

        self.list_widget = QListWidget()
        self.list_widget.addItems(errors)
        layout.addWidget(self.list_widget)

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
