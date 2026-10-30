import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Instance et affichage de la fenêtre principale
    window = MainWindow()
    window.show()

    sys.exit(app.exec())