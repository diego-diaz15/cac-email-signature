"""Main window: form, live preview, copy and export actions."""

from __future__ import annotations

import logging
import tempfile
import webbrowser
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from signature_builder.core.asset_manager import AssetManager
from signature_builder.core.clipboard_manager import copy_html_to_clipboard, signature_plain_text
from signature_builder.core.config_manager import load_brand_config
from signature_builder.core.export_manager import ExportManager
from signature_builder.core.models import PersonData
from signature_builder.core.signature_generator import SignatureGenerator
from signature_builder.ui.form_panel import FormPanel
from signature_builder.ui.preview_panel import PreviewPanel
from signature_builder.ui.styles import APP_STYLESHEET

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Desktop shell. Brand is loaded automatically; the user only fills personal data."""

    def __init__(self) -> None:
        super().__init__()
        self.brand = load_brand_config()
        self.assets = AssetManager(self.brand)
        self.generator = SignatureGenerator(self.brand, self.assets)
        self.exporter = ExportManager(self.brand, self.generator, self.assets)

        self.setWindowTitle(f"Signature Builder · {self.brand.short_name or self.brand.name}")
        self.resize(1180, 760)
        self.setMinimumSize(960, 640)

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.form = FormPanel(email_domain=self.brand.email_domain)
        self.preview = PreviewPanel(self.generator, self.exporter)
        splitter.addWidget(self.form)
        splitter.addWidget(self._preview_with_actions())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([360, 820])
        outer.addWidget(splitter)

        self.statusBar().showMessage("Completá tus datos y pulsá Copiar firma.")
        self.form.data_changed.connect(self._on_form_changed)
        self.form.set_defaults(PersonData(website=self.brand.website.replace("https://", "").replace("www.", "")))
        self._warn_if_missing_assets()

    def _on_form_changed(self, person: PersonData) -> None:
        """Keep the live preview on the selected signature model."""
        self.brand.template = self.form.template()
        self.preview.update_person(person, template=self.brand.template)

    def _selected_template(self) -> str:
        chosen = self.form.template()
        self.brand.template = chosen
        return chosen

    def _preview_with_actions(self) -> QWidget:
        pane = QWidget()
        self.preview.setParent(pane)
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.preview, 1)

        bar = QWidget()
        bar.setObjectName("PreviewPane")
        actions = QHBoxLayout(bar)
        actions.setContentsMargins(32, 0, 32, 24)
        actions.setSpacing(10)

        copy_btn = QPushButton("Copiar firma")
        copy_btn.setObjectName("Primary")
        copy_btn.clicked.connect(self.on_copy)

        open_btn = QPushButton("Ver en el navegador")
        open_btn.setObjectName("Secondary")
        open_btn.clicked.connect(self.on_open_browser)

        html_btn = QPushButton("Exportar HTML")
        html_btn.setObjectName("Ghost")
        html_btn.clicked.connect(self.on_export_html)

        zip_btn = QPushButton("Exportar ZIP")
        zip_btn.setObjectName("Ghost")
        zip_btn.clicked.connect(self.on_export_zip)

        actions.addWidget(copy_btn)
        actions.addWidget(open_btn)
        actions.addWidget(html_btn)
        actions.addWidget(zip_btn)
        actions.addStretch(1)
        layout.addWidget(bar)
        return pane

    def on_copy(self) -> None:
        """Copy the formatted signature so Gmail receives HTML, not only the name."""
        person = self.form.person()
        fragment = self.generator.render_fragment(
            person, image_mode="hosted", template=self._selected_template()
        )
        plain = signature_plain_text(
            person.full_name(),
            person.title,
            person.department,
            self.brand.name,
            person.phone,
            person.email,
            person.website,
        )
        copy_html_to_clipboard(fragment, plain)
        self.statusBar().showMessage("Firma copiada. Pegala en Gmail con Ctrl+V.", 8000)

    def on_open_browser(self) -> None:
        """Open a Gmail-ready HTML (public logo + icons) so copying from the browser keeps images."""
        person = self.form.person()
        dest = Path(tempfile.mkdtemp(prefix="signature-builder-"))
        html_path = self.exporter.export_folder(
            dest, person, image_mode="hosted", template=self._selected_template()
        )
        webbrowser.open(html_path.as_uri())
        self.statusBar().showMessage("Se abrió el navegador. Seleccioná la firma y copiá.", 8000)

    def on_export_html(self) -> None:
        person = self.form.person()
        dest = QFileDialog.getExistingDirectory(self, "Carpeta de exportación")
        if not dest:
            return
        html_path = self.exporter.export_folder(
            Path(dest), person, template=self._selected_template()
        )
        QMessageBox.information(self, "Exportado", f"Se guardó:\n{html_path}")

    def on_export_zip(self) -> None:
        person = self.form.person()
        path, _ = QFileDialog.getSaveFileName(self, "Exportar ZIP", "firma.zip", "ZIP (*.zip)")
        if not path:
            return
        zip_path = self.exporter.export_zip(Path(path), person, template=self._selected_template())
        QMessageBox.information(self, "Exportado", f"Se guardó:\n{zip_path}")

    def _warn_if_missing_assets(self) -> None:
        missing = self.assets.missing_required()
        if not missing:
            return
        self.statusBar().showMessage(
            "Faltan assets de marca. Ejecutá: python -m signature_builder --build-assets",
            0,
        )


def run() -> int:
    """Start the Qt application. Returns the process exit code."""
    import sys

    from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
    from PySide6.QtWebEngineWidgets import QWebEngineView  # noqa: F401

    app = QApplication.instance() or QApplication(sys.argv)
    allow = QWebEngineSettings.ImageAnimationPolicy.Allow
    QWebEngineProfile.defaultProfile().settings().setImageAnimationPolicy(allow)
    app.setApplicationName("Signature Builder")
    app.setStyleSheet(APP_STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec()
