from PyQt5.QtWidgets import QLabel, QWidget, QLineEdit, QPushButton, QCheckBox, QGridLayout, QMdiSubWindow
from PyQt5.QtCore import pyqtSignal, Qt
from resources.fonts import OPTIONS_TITLE_FONT

class OptionsWindow(QMdiSubWindow):
    """
    A submenu for users to manage options for slope, tolerance, and legend visibility.
    """
    # Signals to communicate changes back to the MainWindow
    options_updated = pyqtSignal(float, float, bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set default values for options
        self.slope_target = 1.0
        self.tolerance = 0.3
        self.show_legend = True

        # Create the base options widget
        content_widget = QWidget()
        content_widget.setFixedHeight(300)
        content_widget.setMinimumWidth(300)

        layout = QGridLayout()

        trim_params_title = QLabel("Trimming Parameters")
        trim_params_title.setFont(OPTIONS_TITLE_FONT)
        layout.addWidget(trim_params_title, 0, 0, 1, 2, alignment= Qt.AlignLeft)

        # Slope input
        slope_label = QLabel("Target Slope (K/s):")
        layout.addWidget(slope_label,  1, 0)
        self.slope_input = QLineEdit()
        self.slope_input.setText(str(self.slope_target))
        self.slope_input.setPlaceholderText("Enter target slope")
        layout.addWidget(self.slope_input, 1, 1)
        self.slope_error_label = QLabel("")
        layout.addWidget(self.slope_error_label, 2, 0, 1, 2)

        # Tolerance input
        tolerance_label = QLabel("Slope Tolerance:")
        layout.addWidget(tolerance_label, 3, 0)
        self.tolerance_input = QLineEdit()
        self.tolerance_input.setText(str(self.tolerance))
        self.tolerance_input.setPlaceholderText("Enter tolerance")
        layout.addWidget(self.tolerance_input, 3, 1)
        self.tolerance_error_label = QLabel("")
        layout.addWidget(self.tolerance_error_label, 4, 0, 1, 2)

        # Legend checkbox
        self.legend_checkbox = QCheckBox("Show Legend")
        self.legend_checkbox.setChecked(self.show_legend)
        layout.addWidget(self.legend_checkbox, 5, 0)

        # Apply button
        apply_button = QPushButton("Apply Changes")
        apply_button.clicked.connect(self.apply_changes)
        layout.addWidget(apply_button, 6, 0, 1, 2)

        # Set the layout for the content widget
        content_widget.setLayout(layout)
        self.setWidget(content_widget)

    def apply_changes(self):
        """Read inputs, updates internal state, and emits the signal with updated options."""
        try:
            self.slope_target = float(self.slope_input.text())
            self.slope_error_label.setText("")
        except ValueError:
            self.slope_error_label.setText("Invalid input for target slope. Using previous value.")
        
        try:
            self.tolerance = float(self.tolerance_input.text())
            self.tolerance_error_label.setText("")
        except ValueError:
            self.tolerance_error_label.setText("Invalid input for tolerance. Using previous value.")

        self.show_legend = self.legend_checkbox.isChecked()

        # Emit the updated options
        self.options_updated.emit(self.slope_target, self.tolerance, self.show_legend)