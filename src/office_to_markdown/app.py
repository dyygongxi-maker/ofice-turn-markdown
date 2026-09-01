from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from .security import ValidationError
from .service import ConversionService


class MainWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Office to Markdown")
        self.root.minsize(680, 170)
        self.source = tk.StringVar()
        self.output = tk.StringVar()
        self.status = tk.StringVar(value="Files stay on this computer.")
        for column in range(3):
            self.root.grid_columnconfigure(column, weight=1 if column == 1 else 0)
        tk.Label(self.root, text="Office file").grid(row=0, column=0, padx=12, pady=12, sticky="w")
        tk.Entry(self.root, textvariable=self.source).grid(
            row=0, column=1, padx=6, pady=12, sticky="ew"
        )
        tk.Button(self.root, text="Choose file", command=self.choose_source).grid(
            row=0, column=2, padx=12, pady=12
        )
        tk.Label(self.root, text="Output folder").grid(row=1, column=0, padx=12, pady=8, sticky="w")
        tk.Entry(self.root, textvariable=self.output).grid(
            row=1, column=1, padx=6, pady=8, sticky="ew"
        )
        tk.Button(self.root, text="Choose folder", command=self.choose_output).grid(
            row=1, column=2, padx=12, pady=8
        )
        tk.Button(self.root, text="Convert", command=self.convert).grid(
            row=2, column=1, padx=6, pady=10
        )
        tk.Label(self.root, textvariable=self.status, anchor="w").grid(
            row=3, column=0, columnspan=3, padx=12, pady=8, sticky="ew"
        )

    def choose_source(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Office files", "*.docx *.pptx *.xlsx")])
        if path:
            self.source.set(path)

    def choose_output(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.output.set(path)

    def convert(self) -> None:
        try:
            result = ConversionService().convert(Path(self.source.get()), Path(self.output.get()))
            self.status.set(f"Created: {result.output_path}")
        except (ValidationError, OSError, ValueError) as error:
            messagebox.showerror("Conversion failed", str(error))

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    window = MainWindow()
    window.run()


if __name__ == "__main__":
    main()
