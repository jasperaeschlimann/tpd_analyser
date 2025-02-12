import os
import shutil
from PyQt5.QtWidgets import QFileDialog, QMessageBox


class FileConverter:
    """
    Handles the logic for converting .asc files to .txt files.
    """
    def __init__(self, parent):
        """
        Initializes the FileConverter.
        :param parent: The parent widget for dialogs.
        """
        self.parent = parent

    def convert_asc_to_txt(self):
        """
        Converts selected .asc files to .txt and saves them in the 'txt_files' folder.
        """
        # Show a file dialog to select files
        file_paths, _ = QFileDialog.getOpenFileNames(
            self.parent,
            "Select .asc Files to Convert",
            "",
            "ASC Files (*.asc);;All Files (*)"
        )

        if not file_paths:
            QMessageBox.information(self.parent, "No Files Selected", "No files were selected for conversion.")
            return

        # Create the 'txt_files' folder if it doesn't exist
        output_folder = "txt_files"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Copy and rename files
        for file_path in file_paths:
            file_name = os.path.basename(file_path)  # Get the file name
            txt_file_name = os.path.splitext(file_name)[0] + ".txt"  # Change extension to .txt
            destination_path = os.path.join(output_folder, txt_file_name)

            # Copy the file to the destination and rename
            shutil.copy(file_path, destination_path)

        # Show a success message
        QMessageBox.information(
            self.parent,
            "Conversion Complete",
            f"Selected files have been converted and saved in the '{output_folder}' folder."
        )
