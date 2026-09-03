"""Live preview of the real signature HTML (Chromium via Qt WebEngine)."""

from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from signature_builder.core.export_manager import ExportManager
from signature_builder.core.models import PersonData
from signature_builder.core.signature_generator import SignatureGenerator

logger = logging.getLogger(__name__)

_COPY_JS = """
(function() {
  const root = document.getElementById('signature-root') || document.body;
  const range = document.createRange();
  range.selectNodeContents(root);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  const ok = document.execCommand('copy');
  sel.removeAllRanges();
  return ok;
})();
"""


class PreviewPanel(QWidget):
    """White email canvas. Loads the exported HTML so images resolve like in a browser."""

    def __init__(
        self,
        generator: SignatureGenerator,
        exporter: ExportManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("PreviewPane")
        self.generator = generator
        self.exporter = exporter
        self._preview_dir = Path(tempfile.mkdtemp(prefix="sb-preview-"))
        self._web = None
        self._pending: PersonData | None = None
        self._template: str | None = None
        self._reload_timer = QTimer(self)
        self._reload_timer.setSingleShot(True)
        self._reload_timer.setInterval(400)
        self._reload_timer.timeout.connect(self._flush_preview)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 20)
        caption = QLabel("Vista previa")
        caption.setObjectName("PreviewCaption")
        layout.addWidget(caption)

        card = QFrame()
        card.setStyleSheet("QFrame { background: #ffffff; border-radius: 12px; }")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)

        try:
            from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
            from PySide6.QtWebEngineWidgets import QWebEngineView

            self._web = QWebEngineView()
            self._web.setMinimumHeight(280)
            allow = QWebEngineSettings.ImageAnimationPolicy.Allow
            for settings in (
                QWebEngineProfile.defaultProfile().settings(),
                self._web.settings(),
                self._web.page().settings(),
            ):
                settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
                settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
                settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
                settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
                settings.setImageAnimationPolicy(allow)
            card_layout.addWidget(self._web)
        except ImportError:
            logger.exception("PySide6-WebEngine no está instalado")
            fallback = QLabel("Instalá PySide6-WebEngine para ver la vista previa real.")
            fallback.setWordWrap(True)
            card_layout.addWidget(fallback)

        layout.addWidget(card, 1)

    def update_person(self, person: PersonData, template: str | None = None) -> None:
        """Rebuild the signature HTML on disk and display it."""
        self._pending = person
        self._template = template
        if self._web is None:
            return
        if self._web.url().isEmpty():
            self._flush_preview()
            return
        self._reload_timer.start()

    def _flush_preview(self) -> None:
        if self._pending is None or self._web is None:
            return
        dest = self._preview_dir
        dest.mkdir(parents=True, exist_ok=True)
        logo_name = Path(self.generator.brand.logo.animated).name
        logo_copy = dest / "assets" / logo_name
        if not logo_copy.is_file():
            self.exporter.export_folder(dest, self._pending, template=self._template)
        html = self.generator.render_document(
            self._pending, image_mode="relative", template=self._template
        )
        html_path = dest / "firma.html"
        previous = html_path.read_text(encoding="utf-8") if html_path.is_file() else ""
        already_loaded = not self._web.url().isEmpty()
        if html == previous and already_loaded:
            return
        html_path.write_text(html, encoding="utf-8")
        if not already_loaded:
            self._web.load(QUrl.fromLocalFile(str(html_path.resolve())))
            return
        fragment = self.generator.render_fragment(
            self._pending, image_mode="relative", template=self._template
        )
        model = json.dumps(self._template or "corporate")
        self._web.page().runJavaScript(
            "var root = document.getElementById('signature-root');"
            "if (root) {"
            f"  root.setAttribute('data-model', {model});"
            f"  root.innerHTML = {json.dumps(fragment)};"
            "}"
        )

    def copy_rendered(self, callback) -> None:
        """Copy the rendered signature via Chromium (same idea as copying from a browser)."""
        if self._web is None:
            callback(False)
            return
        self._web.page().runJavaScript(_COPY_JS, 0, callback)
