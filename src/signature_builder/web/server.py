"""Local HTTP server for the CAC signature builder web UI."""

from __future__ import annotations

import io
import json
import logging
import mimetypes
import threading
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from signature_builder.core.asset_manager import AssetManager
from signature_builder.core.clipboard_manager import signature_plain_text
from signature_builder.core.config_manager import load_brand_config
from signature_builder.core.models import BrandConfig, PersonData
from signature_builder.core.signature_generator import SignatureGenerator
from signature_builder.core.template_engine import normalize_template
from signature_builder.web.payload import person_from_payload, template_from_payload

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_BODY = 64 * 1024


class SignatureWebApp:
    """Shared generator + brand for every HTTP request."""

    def __init__(self, brand: BrandConfig | None = None, root: Path | None = None) -> None:
        self.brand = brand or load_brand_config()
        self.assets = AssetManager(self.brand, root=root)
        self.generator = SignatureGenerator(self.brand, self.assets)

    def meta(self) -> dict[str, str]:
        website = self.brand.website.replace("https://", "").replace("http://", "").replace("www.", "")
        return {
            "name": self.brand.name,
            "short_name": self.brand.short_name or self.brand.name,
            "email_domain": self.brand.email_domain,
            "website": website,
        }

    def render_bundle(
        self,
        person: PersonData,
        image_mode: str = "hosted",
        template: str | None = None,
    ) -> dict[str, str]:
        chosen = normalize_template(template or self.brand.template)
        fragment = self.generator.render_fragment(person, image_mode=image_mode, template=chosen)
        document = self.generator.render_document(person, image_mode=image_mode, template=chosen)
        plain = signature_plain_text(
            person.full_name(),
            person.title,
            person.department,
            self.brand.name,
            person.phone,
            person.email,
            person.website,
        )
        return {
            "fragment": fragment,
            "document": document,
            "plain": plain,
            "template": chosen,
        }

    def export_zip_bytes(self, person: PersonData, template: str | None = None) -> bytes:
        buffer = io.BytesIO()
        html = self.generator.render_document(person, image_mode="relative", template=template)
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("firma.html", html)
            logo = self.assets.logo_animated_path()
            archive.write(logo, arcname=f"assets/{logo.name}")
            static = self.assets.resolve(self.brand.logo.static)
            if static.is_file():
                archive.write(static, arcname=f"assets/{static.name}")
            for key in ("phone", "email", "web", "linkedin"):
                try:
                    icon = self.assets.icon_path(key)
                except Exception:
                    continue
                archive.write(icon, arcname=f"assets/{icon.name}")
        return buffer.getvalue()


def make_handler(app: SignatureWebApp) -> type[BaseHTTPRequestHandler]:
    """Bind one SignatureWebApp instance to a request handler class."""

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            logger.info("%s - %s", self.address_string(), format % args)

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path in ("/", "/index.html"):
                self._send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
                return
            if path == "/api/meta":
                self._send_json(200, app.meta())
                return
            if path.startswith("/static/"):
                self._send_static(path[len("/static/") :])
                return
            self._send_json(404, {"error": "No encontrado"})

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            try:
                raw = self._read_json()
                person = person_from_payload(raw, app.brand.email_domain)
                template = template_from_payload(raw)
            except ValueError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            if path == "/api/preview":
                self._send_json(200, app.render_bundle(person, image_mode="hosted", template=template))
                return
            if path == "/api/export.html":
                html = app.generator.render_document(person, image_mode="relative", template=template)
                payload = html.encode("utf-8")
                self._send_bytes(200, payload, "text/html; charset=utf-8", "firma.html")
                return
            if path == "/api/export.zip":
                payload = app.export_zip_bytes(person, template=template)
                self._send_bytes(200, payload, "application/zip", "firma.zip")
                return
            self._send_json(404, {"error": "No encontrado"})

        def _read_json(self) -> Any:
            length = int(self.headers.get("Content-Length") or "0")
            if length < 0 or length > MAX_BODY:
                raise ValueError("El pedido es demasiado grande")
            raw = self.rfile.read(length) if length else b"{}"
            try:
                return json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as exc:
                raise ValueError("JSON inválido") from exc

        def _send_static(self, relative: str) -> None:
            target = (STATIC_DIR / relative).resolve()
            if STATIC_DIR not in target.parents or not target.is_file():
                self._send_json(404, {"error": "No encontrado"})
                return
            mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            if target.suffix == ".js":
                mime = "text/javascript; charset=utf-8"
            elif target.suffix == ".css":
                mime = "text/css; charset=utf-8"
            self._send_file(target, mime)

        def _send_file(self, path: Path, content_type: str) -> None:
            if not path.is_file():
                self._send_json(404, {"error": "No encontrado"})
                return
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.end_headers()
            self.wfile.write(data)

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _send_bytes(self, status: int, payload: bytes, content_type: str, filename: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

    return Handler


def serve(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    """Start the web UI and block until interrupted."""
    app = SignatureWebApp()
    handler = make_handler(app)
    httpd = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{port}/"
    logger.info("Firmador web en %s", url)
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Firmador web detenido")
    finally:
        httpd.server_close()
