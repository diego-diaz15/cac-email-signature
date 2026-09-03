"""CF_HTML wrapper used as a clipboard fallback."""

from signature_builder.core.clipboard_manager import signature_plain_text, wrap_cf_html


def _header_offsets(wrapped: str) -> dict[str, int]:
    offsets: dict[str, int] = {}
    for line in wrapped.split("\r\n"):
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        if key in {"StartHTML", "EndHTML", "StartFragment", "EndFragment"}:
            offsets[key] = int(value)
        if line.startswith("<html"):
            break
    return offsets


def test_wrap_cf_html_contains_fragment_markers() -> None:
    wrapped = wrap_cf_html("<table><tr><td>Hola</td></tr></table>")
    assert "StartHTML:" in wrapped
    assert "<!--StartFragment-->" in wrapped
    assert "<table>" in wrapped
    assert wrapped.index("<!--StartFragment-->") < wrapped.index("<table>")


def test_wrap_cf_html_uses_utf8_byte_offsets() -> None:
    fragment = "<table><tr><td>Cámara Argentina</td></tr></table>"
    wrapped = wrap_cf_html(fragment)
    raw = wrapped.encode("utf-8")
    offsets = _header_offsets(wrapped)
    start_html = offsets["StartHTML"]
    end_html = offsets["EndHTML"]
    start_fragment = offsets["StartFragment"]
    end_fragment = offsets["EndFragment"]
    assert raw[start_fragment:end_fragment] == fragment.encode("utf-8")
    assert raw[start_html:start_html + 6] == b"<html>"
    assert raw[end_html - 7 : end_html] == b"</html>"
    assert len(fragment) != len(fragment.encode("utf-8"))


def test_signature_plain_text_keeps_contact_lines() -> None:
    text = signature_plain_text("Diego Diaz", "Soporte", "", "CAC", "11 5300-9000", "ddiaz@cac.com.ar")
    assert text == "Diego Diaz\nSoporte\nCAC\n11 5300-9000\nddiaz@cac.com.ar"
