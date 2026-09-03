"""Web firmador: same generator, locked email domain, hosted copy HTML."""

from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

from signature_builder.core.models import BrandConfig
from signature_builder.web.payload import person_from_payload
from signature_builder.web.server import SignatureWebApp, make_handler


def _start(app: SignatureWebApp) -> tuple[ThreadingHTTPServer, str]:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(app))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address[:2]
    return httpd, f"http://{host}:{port}"


def _json(url: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, method="GET" if data is None else "POST")
    if data is not None:
        request.add_header("Content-Type", "application/json")
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def test_person_from_payload_locks_org_domain() -> None:
    person = person_from_payload(
        {
            "first_name": "Diego",
            "email_local": "ddiaz@otro.com",
            "email": "hacker@evil.com",
            "website": "javascript:alert(1)",
            "linkedin": "https://www.linkedin.com/in/ejemplo",
        },
        "cac.com.ar",
    )
    assert person.email == "ddiaz@cac.com.ar"
    assert person.first_name == "Diego"


def test_web_home_and_preview_use_hosted_logo(brand: BrandConfig, brand_dir: Path) -> None:
    brand.logo.public_url = "https://cdn.example.com/logo-cac.gif"
    app = SignatureWebApp(brand=brand, root=brand_dir)
    httpd, origin = _start(app)
    try:
        with urlopen(origin + "/", timeout=10) as response:
            page = response.read().decode("utf-8")
        assert "Signature Builder" in page
        assert 'name="email_local"' in page
        assert 'name="template"' in page
        assert "/static/app.js?v=4" in page
        meta = _json(origin + "/api/meta")
        assert meta["email_domain"] == "cac.com.ar"
        body = _json(
            origin + "/api/preview",
            {
                "first_name": "María",
                "last_name": "González",
                "email_local": "maria.gonzalez",
                "linkedin": "https://www.linkedin.com/in/ejemplo",
            },
        )
        assert "https://cdn.example.com/logo-cac.gif" in body["fragment"]
        assert "file:" not in body["fragment"]
        assert "javascript:" not in body["fragment"]
        assert "maria.gonzalez@cac.com.ar" in body["fragment"]
        assert "data:image" in body["fragment"]
        assert "<!DOCTYPE html>" in body["document"]
        original = _json(
            origin + "/api/preview",
            {
                "first_name": "María",
                "title": "Soporte Técnico",
                "email_local": "maria.gonzalez",
                "template": "original",
            },
        )
        assert "Argentina de" in original["fragment"]
        assert original["fragment"].find("Soporte Técnico") < original["fragment"].find("logo-cac.gif")
        assert original["template"] == "original"
        assert 'data-model="original"' in original["document"]
        assert original["fragment"].find("maria.gonzalez") < original["fragment"].find("logo-cac.gif")
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_web_export_zip_contains_html(brand: BrandConfig, brand_dir: Path) -> None:
    app = SignatureWebApp(brand=brand, root=brand_dir)
    httpd, origin = _start(app)
    try:
        request = Request(
            origin + "/api/export.zip",
            data=json.dumps({"first_name": "Ana"}).encode("utf-8"),
            method="POST",
        )
        request.add_header("Content-Type", "application/json")
        with urlopen(request, timeout=10) as response:
            payload = response.read()
            assert response.headers.get("Content-Type") == "application/zip"
        assert payload[:2] == b"PK"
        assert b"firma.html" in payload
    finally:
        httpd.shutdown()
        httpd.server_close()
