from PyQt5.QtWidgets import (
    QWidget, QMdiSubWindow,
    QMessageBox
)
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic

class TrimmingOptionsWindow(QMdiSubWindow):
    """
    A submenu for users to manage options for slope, tolerance, smoothing, and legend visibility.
    """
    # Signal to communicate changes back to the MainWindow
    options_updated = pyqtSignal(float, float, bool, int)

    def __init__(self, parent=None):
        # Call QMdiSubWindow constructor
        super().__init__(parent)

        # Set default values for options
        self.slope_target = 1.0
        self.tolerance = 0.3
        self.smoothing_enabled = False
        self.smoothing_window = 10

        # Initialise UI for trimming options
        self.content_widget = QWidget()
        uic.loadUi("gui/trimming_options_window.ui", self.content_widget)
        self.content_widget.checkBox_EnableSmoothing.toggled.connect(self.toggle_smoothing_inputs)
        self.content_widget.pushButton_ApplyChanges.clicked.connect(self.apply_changes)
        self.content_widget.lineEdit_SmoothingWindow.setEnabled(self.smoothing_enabled)
        self.setWidget(self.content_widget)
        self.setAttribute(0x00000002) # Qt.WA_DeleteOnClose

    def toggle_smoothing_inputs(self, enabled):
        """Enable or disable smoothing parameter inputs."""
        self.content_widget.lineEdit_SmoothingWindow.setEnabled(enabled)

    def apply_changes(self):
        """Read inputs, updates internal state, and emits the signal with updated options."""
        errors = []
        try:
            self.slope_target = float(self.content_widget.lineEdit_TargetSlope.text())
        except ValueError:
            errors.append("Invalid input for Target Slope. Please enter a valid number.")

        try:
            self.tolerance = float(self.content_widget.lineEdit_SlopeTolerance.text())
        except ValueError:
            errors.append("Invalid input for Tolerance. Please enter a valid number.")

        self.smoothing_enabled = self.content_widget.checkBox_EnableSmoothing.isChecked()

        if self.smoothing_enabled:
            try:
                self.smoothing_window = int(self.content_widget.lineEdit_SmoothingWindow.text())
                if self.smoothing_window <= 0:
                    raise ValueError
            except ValueError:
                errors.append("Invalid input for Smoothing Window. Please enter a positive integer.")

        # Display errors if any
        if errors:
            QMessageBox.information(self, "Input Error", "\n".join(errors))
            return

        # Emit the updated options
        self.options_updated.emit(
            self.slope_target, self.tolerance, self.smoothing_enabled, self.smoothing_window
        )
        QMessageBox.information(self, "Success", "Options successfully updated!")
