"""Tests for HTML escaping, URL rules and email detection."""

from signature_builder.core.sanitizer import (
    compose_org_email,
    escape_text,
    looks_like_email,
    normalize_http_url,
    normalize_mailto,
    normalize_tel,
)


def test_escape_text_escapes_html_special_chars() -> None:
    assert escape_text('<script>alert("x")</script>') == "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;"
    assert "&amp;" in escape_text("A & B")
    assert escape_text("  hola  ") == "hola"


def test_normalize_http_url_adds_https_and_rejects_javascript() -> None:
    assert normalize_http_url("cac.com.ar") == "https://cac.com.ar"
    assert normalize_http_url("https://www.cac.com.ar/path") == "https://www.cac.com.ar/path"
    assert normalize_http_url("javascript:alert(1)") == ""
    assert normalize_http_url("data:text/html,hi") == ""
    assert normalize_http_url("") == ""


def test_normalize_mailto_and_tel() -> None:
    assert normalize_mailto("juan@cac.com.ar") == "mailto:juan@cac.com.ar"
    assert normalize_mailto("not-an-email") == ""
    assert normalize_tel("+54 11 5300-9000").startswith("tel:+5411")
    assert normalize_tel("abc") == ""


def test_looks_like_email() -> None:
    assert looks_like_email("a@b.com")
    assert not looks_like_email("a@b")
    assert not looks_like_email("")


def test_compose_org_email_uses_static_domain() -> None:
    assert compose_org_email("ddiaz") == "ddiaz@cac.com.ar"
    assert compose_org_email("ddiaz@gmail.com") == "ddiaz@cac.com.ar"
    assert compose_org_email("  DDIAZ  ") == "DDIAZ@cac.com.ar"
    assert compose_org_email("") == ""
