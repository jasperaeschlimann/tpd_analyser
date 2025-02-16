from PyQt5.QtWidgets import (
    QWidget, QMdiSubWindow,
    QMessageBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic

class TrimmingOptionsWindow(QMdiSubWindow):
    """
    A submenu for users to configure trimming options such as:
    - Target slope
    - Tolerance
    - Smoothing (on/off)
    - Smoothing window size

    Emits a signal `options_updated` when changes are applied.
    """
    # Signal to communicate updated trimming options to the main window
    options_updated = pyqtSignal(float, float, bool, int)

    def __init__(self):
        """
        Initialises the TrimmingOptionsWindow UI and sets default trimming options.
        """
        super().__init__()

        # Default trimming parameters
        self.slope_target = 1.0 # Target temperature slope
        self.tolerance = 0.3    # Acceptable deviation from the target slope
        self.smoothing_enabled = False  # Whether smoothing filter is applied
        self.smoothing_window = 10  # Window size for smoothing

        # Load UI
        self.content_widget = QWidget()
        uic.loadUi("gui/trimming_options_window.ui", self.content_widget)
        self.setWindowIcon(QIcon("resources/icons/options.png"))
        self.setWidget(self.content_widget)
        self.setAttribute(0x00000002) # Qt.WA_DeleteOnClose

        # Connect UI elements to methods
        self.content_widget.checkBox_EnableSmoothing.toggled.connect(self._toggle_smoothing_inputs)
        self.content_widget.pushButton_ApplyChanges.clicked.connect(self.apply_changes)

        # Disable smoothing input by default
        self.content_widget.lineEdit_SmoothingWindow.setEnabled(self.smoothing_enabled)

    def _toggle_smoothing_inputs(self, enabled):
        """
        Enables or disables the smoothing window input based on checkbox state.

        :param enabled: Boolean indicating whether smoothing is enabled
        """
        self.content_widget.lineEdit_SmoothingWindow.setEnabled(enabled)

    def apply_changes(self):
        """
        Reads user input, validates values, updates internal state,
        and emits a signal with the new options.
        """        
        errors = []

        # Validate target slope input
        try:
            self.slope_target = float(self.content_widget.lineEdit_TargetSlope.text())
        except ValueError:
            errors.append("Invalid input for Target Slope.\nPlease enter a valid number.\n")

        # Validate tolerance input
        try:
            self.tolerance = float(self.content_widget.lineEdit_SlopeTolerance.text())
        except ValueError:
            errors.append("Invalid input for Tolerance.\nPlease enter a valid number.\n")

        # Get smoothing settings
        self.smoothing_enabled = self.content_widget.checkBox_EnableSmoothing.isChecked()

        # Validate smoothing window input if smoothing is enabled
        if self.smoothing_enabled:
            try:
                self.smoothing_window = int(self.content_widget.lineEdit_SmoothingWindow.text())
                if self.smoothing_window <= 0:
                    raise ValueError
            except ValueError:
                errors.append("Invalid input for Smoothing Window.\nPlease enter a positive integer.\n")

        # Display error messages if any validation failed
        if errors:
            QMessageBox.information(self, "Input Error", "\n".join(errors))
            return

        # Emit updated trimming parameters
        self.options_updated.emit(
            self.slope_target, self.tolerance, self.smoothing_enabled, self.smoothing_window
        )
