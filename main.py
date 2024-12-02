import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    # Initialize the application
    app = QApplication(sys.argv)

    # Create an instance of the main window
    window = MainWindow()
    window.show()

    # Execute the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()