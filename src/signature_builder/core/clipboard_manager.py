"""Copy signature HTML as rich text so Gmail/Outlook can paste a formatted signature."""

from __future__ import annotations

import logging
import re
import sys
import time

logger = logging.getLogger(__name__)

_HEADER = (
    "Version:0.9\r\n"
    "StartHTML:{:09d}\r\n"
    "EndHTML:{:09d}\r\n"
    "StartFragment:{:09d}\r\n"
    "EndFragment:{:09d}\r\n"
)
_PREFIX = "<html>\r\n<head><meta charset=\"utf-8\"></head>\r\n<body>\r\n<!--StartFragment-->"
_SUFFIX = "<!--EndFragment-->\r\n</body>\r\n</html>"


def wrap_cf_html(fragment: str) -> str:
    """Wrap a signature table in Windows CF_HTML using UTF-8 byte offsets."""
    header_len = len(_HEADER.format(0, 0, 0, 0).encode("utf-8"))
    prefix_len = len(_PREFIX.encode("utf-8"))
    fragment_len = len(fragment.encode("utf-8"))
    suffix_len = len(_SUFFIX.encode("utf-8"))
    start_html = header_len
    start_fragment = start_html + prefix_len
    end_fragment = start_fragment + fragment_len
    end_html = start_html + prefix_len + fragment_len + suffix_len
    header = _HEADER.format(start_html, end_html, start_fragment, end_fragment)
    return header + _PREFIX + fragment + _SUFFIX


def clipboard_document(fragment: str) -> str:
    """Full HTML document for text/html clipboard payloads."""
    return (
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\"></head>"
        f"<body>{fragment}</body></html>"
    )


def signature_plain_text(*lines: str) -> str:
    """Plain-text fallback with every non-empty line, not just the name."""
    return "\n".join(part.strip() for part in lines if (part or "").strip())


def copy_html_to_clipboard(html_fragment: str, plain_text: str = "") -> None:
    """Put CF_HTML + text/html + a full text fallback on the clipboard.

    Chrome/Gmail on Windows read the ``HTML Format`` clipboard type and ignore
    ``text/html`` if those UTF-8 byte offsets are wrong. They then paste
    ``text/plain`` — which used to be only the person's name.
    """
    document = clipboard_document(html_fragment)
    cf_html = wrap_cf_html(html_fragment)
    plain = plain_text or _plain_fallback(html_fragment)

    if sys.platform == "win32":
        try:
            _copy_windows_clipboard(cf_html, document, plain)
            logger.info("Firma copiada al portapapeles (%s chars HTML)", len(html_fragment))
            return
        except OSError:
            logger.exception("Portapapeles nativo de Windows falló; se intenta Qt")

    _copy_qt_clipboard(cf_html, document, plain)
    logger.info("Firma copiada al portapapeles (%s chars HTML)", len(html_fragment))


def _copy_windows_clipboard(cf_html: str, document: str, plain: str) -> None:
    """Set CF_HTML with correct UTF-8 offsets via the Win32 clipboard API."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    gmem_moveable = 0x0002
    cf_unicode_text = 13

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.RegisterClipboardFormatW.argtypes = [wintypes.LPCWSTR]
    user32.RegisterClipboardFormatW.restype = wintypes.UINT
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.restype = wintypes.HGLOBAL

    def alloc_bytes(payload: bytes) -> int:
        handle = kernel32.GlobalAlloc(gmem_moveable, len(payload))
        if not handle:
            raise OSError("GlobalAlloc falló")
        locked = kernel32.GlobalLock(handle)
        if not locked:
            kernel32.GlobalFree(handle)
            raise OSError("GlobalLock falló")
        try:
            ctypes.memmove(locked, payload, len(payload))
        finally:
            kernel32.GlobalUnlock(handle)
        return handle

    def set_format(fmt: int, payload: bytes) -> None:
        handle = alloc_bytes(payload)
        if not user32.SetClipboardData(fmt, handle):
            kernel32.GlobalFree(handle)
            raise OSError("SetClipboardData falló")

    cf_html_fmt = user32.RegisterClipboardFormatW("HTML Format")
    text_html_fmt = user32.RegisterClipboardFormatW("text/html")
    if not cf_html_fmt:
        raise OSError("No se pudo registrar HTML Format")

    opened = False
    for _ in range(20):
        if user32.OpenClipboard(None):
            opened = True
            break
        time.sleep(0.05)
    if not opened:
        raise OSError("OpenClipboard falló")

    try:
        if not user32.EmptyClipboard():
            raise OSError("EmptyClipboard falló")
        set_format(cf_html_fmt, cf_html.encode("utf-8") + b"\x00")
        if text_html_fmt:
            set_format(text_html_fmt, document.encode("utf-8") + b"\x00")
        set_format(cf_unicode_text, plain.encode("utf-16-le") + b"\x00\x00")
    finally:
        user32.CloseClipboard()


def _copy_qt_clipboard(cf_html: str, document: str, plain: str) -> None:
    """Qt fallback. Do not call setHtml: it rewrites CF_HTML with character offsets."""
    from PySide6.QtCore import QByteArray, QMimeData
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        raise RuntimeError("No hay QApplication; no se puede usar el portapapeles")

    mime = QMimeData()
    mime.setData("HTML Format", QByteArray(cf_html.encode("utf-8")))
    mime.setData("text/html", QByteArray(document.encode("utf-8")))
    mime.setText(plain)
    app.clipboard().setMimeData(mime)


def _plain_fallback(html_fragment: str) -> str:
    """Very small HTML-to-text fallback for clipboard text/plain."""
    text = re.sub(r"<br\s*/?>", "\n", html_fragment, flags=re.I)
    text = re.sub(r"</(div|p|tr)>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return "\n".join(part for part in (line.strip() for line in text.splitlines()) if part)
