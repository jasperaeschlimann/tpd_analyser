from PyQt5.QtWidgets import QDockWidget, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QPushButton, QCheckBox
from PyQt5.QtCore import pyqtSignal

class OptionsPane(QDockWidget):
    """A dockable widget to manage user options for slope, tolerance, and legend visibility."""
    
    # Signals to communicate changes back to the MainWindow
    options_updated = pyqtSignal(float, float, bool)

    def __init__(self, parent=None):
        super().__init__("Options", parent)

        # Set default values for options
        self.slope_target = 1.0
        self.tolerance = 0.3
        self.show_legend = True

        # Create the base options widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        trimming_params_widget = QWidget()
        trim_params_layout = QVBoxLayout(trimming_params_widget)

        trim_params_title = QLabel("Trimming Parameters")
        trim_params_layout.addWidget(trim_params_title)
        # Slope input
        slope_widget = QWidget()
        slope_layout = QHBoxLayout(slope_widget)
        slope_label = QLabel("Target Slope (K/s):")
        slope_layout.addWidget(slope_label)
        self.slope_input = QLineEdit()
        self.slope_input.setText(str(self.slope_target))
        self.slope_input.setPlaceholderText("Enter target slope")
        slope_layout.addWidget(self.slope_input)
        trim_params_layout.addWidget(slope_widget)
        self.slope_error_label = QLabel("")
        trim_params_layout.addWidget(self.slope_error_label)

        # Tolerance input
        tolerance_widget = QWidget()
        tolerance_layout = QHBoxLayout(tolerance_widget)
        tolerance_label = QLabel("Slope Tolerance:")
        tolerance_layout.addWidget(tolerance_label)
        self.tolerance_input = QLineEdit()
        self.tolerance_input.setText(str(self.tolerance))
        self.tolerance_input.setPlaceholderText("Enter tolerance")
        tolerance_layout.addWidget(self.tolerance_input)
        trim_params_layout.addWidget(tolerance_widget)
        self.tolerance_error_label = QLabel("")
        trim_params_layout.addWidget(self.tolerance_error_label)

        layout.addWidget(trimming_params_widget)

        # Legend checkbox
        self.legend_checkbox = QCheckBox("Show Legend")
        self.legend_checkbox.setChecked(self.show_legend)
        layout.addWidget(self.legend_checkbox)

        # Apply button
        apply_button = QPushButton("Apply Changes")
        apply_button.clicked.connect(self.apply_changes)
        layout.addWidget(apply_button)

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