from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QSizePolicy


class Status(QLabel):
    def __init__(self, parent=None):
        super().__init__(text="Statut : en attente" , parent=parent)
        self.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.setStyleSheet("""
                    QLabel {
                        color: #AAAAAA;
                        font-style: italic;
                    }
                """)
        self.setSizePolicy(
            QSizePolicy.Maximum,
            QSizePolicy.Fixed
        )

    def set_status(self, text, state="idle"):
        self.setText(f"Statut : {text}")

        colors = {
            "idle": "#AAAAAA",
            "working": "#4FC3F7",
            "done": "#81C784",
            "error": "#E57373",
        }

        self.setStyleSheet(f"""
            QLabel {{
                color: {colors.get(state, "#AAAAAA")};
                font-style: italic;
            }}
        """)