from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .security import ValidationError
from .service import ConversionService


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Office to Markdown")
        self.setMinimumWidth(680)

        self.source_input = QLineEdit()
        self.output_input = QLineEdit()
        self.status_label = QLabel("Files stay on this computer.")
        self.status_label.setWordWrap(True)

        source_button = QPushButton("Choose file")
        source_button.clicked.connect(self.choose_source)
        output_button = QPushButton("Choose folder")
        output_button.clicked.connect(self.choose_output)
        convert_button = QPushButton("Convert")
        convert_button.clicked.connect(self.convert)

        source_row = QHBoxLayout()
        source_row.addWidget(self.source_input)
        source_row.addWidget(source_button)
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_input)
        output_row.addWidget(output_button)

        form = QFormLayout()
        form.addRow("Office file", source_row)
        form.addRow("Output folder", output_row)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(convert_button)
        layout.addWidget(self.status_label)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def choose_source(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Office file",
            filter="Office files (*.docx *.pptx *.xlsx)",
        )
        if path:
            self.source_input.setText(path)

    def choose_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choose output folder")
        if path:
            self.output_input.setText(path)

    def convert(self) -> None:
        try:
            result = ConversionService().convert(
                Path(self.source_input.text()), Path(self.output_input.text())
            )
        except (ValidationError, OSError, ValueError) as error:
            QMessageBox.critical(self, "Conversion failed", str(error))
            return
        self.status_label.setText(f"Created: {result.output_path}")


def main() -> None:
    application = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    raise SystemExit(application.exec())


if __name__ == "__main__":
    main()
