import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from gui.main_window import MainWindow

def main():
    # Initialize the application
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("resources/TPD.ico"))
    # Create an instance of the main window
    window = MainWindow()
    window.show()

    # Execute the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()