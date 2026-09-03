"""Build email-safe signature HTML from person data + brand + template."""

from __future__ import annotations

import logging
from pathlib import Path

from signature_builder.core.asset_manager import AssetManager
from signature_builder.core.models import BrandConfig, PersonData
from signature_builder.core.sanitizer import (
    escape_text,
    looks_like_email,
    normalize_http_url,
    normalize_mailto,
    normalize_tel,
)
from signature_builder.core.template_engine import load_template, normalize_template, render_template

logger = logging.getLogger(__name__)

SOCIAL_META = (("linkedin", "LinkedIn"),)

IMG_STYLE = (
    "display:block;border:0;outline:none;text-decoration:none;"
    "background-color:transparent;"
)
ROW_FONT = "font-family:{font};font-size:12px;line-height:16px;"


class SignatureGenerator:
    """Compose signature HTML. UI must not build markup itself."""

    def __init__(self, brand: BrandConfig, assets: AssetManager | None = None) -> None:
        self.brand = brand
        self.assets = assets or AssetManager(brand)

    def render_fragment(self, person: PersonData, image_mode: str = "file", template: str | None = None) -> str:
        """Return the signature table only (what Gmail/Outlook should receive)."""
        template_name = normalize_template(template or self.brand.template)
        markup = load_template(template_name)
        context = self._context(person, image_mode=image_mode, template_name=template_name)
        html = render_template(markup, context)
        logger.debug("Firma generada (%s, %s chars)", template_name, len(html))
        return html.strip()

    def render_document(
        self,
        person: PersonData,
        image_mode: str = "file",
        template: str | None = None,
    ) -> str:
        """Return a full HTML document for preview and browser export."""
        template_name = normalize_template(template or self.brand.template)
        fragment = self.render_fragment(person, image_mode=image_mode, template=template_name)
        return (
            "<!DOCTYPE html>\n"
            '<html lang="es">\n'
            "<head>\n"
            '  <meta charset="utf-8">\n'
            "  <title>Firma</title>\n"
            "</head>\n"
            '<body style="margin:0;padding:24px;background:#ffffff;">\n'
            f'<div id="signature-root" data-model="{template_name}">{fragment}</div>\n'
            "</body>\n"
            "</html>\n"
        )

    def _context(self, person: PersonData, image_mode: str, template_name: str = "corporate") -> dict[str, str]:
        colors = self.brand.colors
        font = "Arial, Helvetica, sans-serif"
        website_raw = person.website.strip() or self.brand.website
        website_url = normalize_http_url(website_raw)
        website_label = escape_text(_display_host(website_raw or self.brand.website))

        name = escape_text(person.full_name())
        title = escape_text(person.title)
        department = escape_text(person.department)
        company = escape_text(self.brand.name)
        line1, line2, line3 = _wordmark_lines(self.brand.name)
        mark_size = 72 if template_name == "original" else self.brand.logo.display_width
        mark_height = 72 if template_name == "original" else self.brand.logo.display_height

        return {
            "font": font,
            "text": colors.text,
            "muted": colors.muted,
            "link": colors.link,
            "divider": colors.divider,
            "primary": colors.primary,
            "name": name,
            "title": title,
            "department": department,
            "company": company,
            "company_line1": line1,
            "company_line2": line2,
            "company_line3": line3,
            "logo_block": self._logo_block(website_url, image_mode, width=mark_size, height=mark_height),
            "website_url": escape_text(website_url),
            "website_label": website_label,
            "contact_web": website_url,
            "web_icon_cell": self._icon_cell("web", image_mode) if website_url else "",
            "phone_row": self._phone_row(person, font, colors.text, image_mode),
            "email_row": self._email_row(person, font, colors.link, image_mode),
            "web_row": self._web_row(website_url, website_label, font, colors.link, image_mode),
            "socials": self._socials_html(person, image_mode),
        }

    def _logo_block(
        self,
        website_url: str,
        image_mode: str,
        width: int | None = None,
        height: int | None = None,
    ) -> str:
        width = width or self.brand.logo.display_width
        height = height or self.brand.logo.display_height
        src = self._logo_src(image_mode)
        if not src:
            return ""
        alt = escape_text(self.brand.short_name or self.brand.name)
        img = (
            f'<img src="{escape_text(src)}" width="{width}" height="{height}" alt="{alt}" '
            f'style="{IMG_STYLE}" />'
        )
        if not website_url:
            return img
        href = escape_text(website_url)
        return (
            f'<a href="{href}" target="_blank" '
            f'style="text-decoration:none;border:0;background-color:transparent;">{img}</a>'
        )

    def _logo_src(self, image_mode: str) -> str:
        """Return the logo URL for this image mode. Hosted mode never uses local files."""
        if image_mode in ("gmail", "hosted"):
            return normalize_http_url(self.brand.logo.public_url)
        path = self.assets.logo_animated_path()
        return self._image_src(path, image_mode)

    def _phone_row(self, person: PersonData, font: str, color: str, image_mode: str) -> str:
        phone = escape_text(person.phone)
        if not phone:
            return ""
        href = normalize_tel(person.phone)
        inner = (
            f'<a href="{escape_text(href)}" style="color:{color};text-decoration:none;">{phone}</a>'
            if href
            else phone
        )
        return self._contact_row(self._icon_cell("phone", image_mode), inner, font)

    def _email_row(self, person: PersonData, font: str, color: str, image_mode: str) -> str:
        raw = person.email.strip()
        if not raw:
            return ""
        label = escape_text(raw)
        href = normalize_mailto(raw) if looks_like_email(raw) else ""
        inner = (
            f'<a href="{escape_text(href)}" style="color:{color};text-decoration:none;">{label}</a>'
            if href
            else label
        )
        return self._contact_row(self._icon_cell("email", image_mode), inner, font)

    def _web_row(
        self,
        website_url: str,
        website_label: str,
        font: str,
        color: str,
        image_mode: str,
    ) -> str:
        if not website_url:
            return ""
        inner = (
            f'<a href="{escape_text(website_url)}" target="_blank" '
            f'style="color:{color};text-decoration:none;">{website_label}</a>'
        )
        return self._contact_row(self._icon_cell("web", image_mode), inner, font)

    def _contact_row(self, icon_cell: str, inner: str, font: str) -> str:
        text_td = (
            f'<td valign="middle" style="padding:0 0 4px 0;{ROW_FONT.format(font=font)}">{inner}</td>'
        )
        if not icon_cell:
            return f"<tr>{text_td}</tr>"
        return (
            "<tr>"
            f'<td valign="middle" width="18" style="padding:0 6px 4px 0;">{icon_cell}</td>'
            f"{text_td}"
            "</tr>"
        )

    def _icon_cell(self, name: str, image_mode: str) -> str:
        src_mode = "data" if image_mode in ("gmail", "hosted") else image_mode
        src = self._icon_src(name, src_mode)
        if not src:
            return ""
        return f'<img src="{src}" width="14" height="14" alt="" style="{IMG_STYLE}" />'

    def _image_src(self, path: Path, image_mode: str) -> str:
        if image_mode == "data":
            return self.assets.data_uri(path)
        if image_mode == "relative":
            return f"assets/{path.name}"
        return self.assets.file_uri(path)

    def _icon_src(self, name: str, image_mode: str) -> str:
        try:
            return self._image_src(self.assets.icon_path(name), image_mode)
        except Exception:
            logger.warning("Icono ausente: %s", name)
            return ""

    def _socials_html(self, person: PersonData, image_mode: str) -> str:
        cells: list[str] = []
        for field_name, label in SOCIAL_META:
            url = normalize_http_url(getattr(person, field_name))
            if not url:
                continue
            if image_mode in ("gmail", "hosted"):
                src = self._icon_src(field_name, "data")
                if not src:
                    continue
                cells.append(
                    '<td style="padding:0 8px 0 0;">'
                    f'<a href="{escape_text(url)}" target="_blank" style="text-decoration:none;">'
                    f'<img src="{src}" width="16" height="16" alt="{escape_text(label)}" '
                    f'style="{IMG_STYLE}" />'
                    "</a></td>"
                )
                continue
            try:
                src = self._image_src(self.assets.icon_path(field_name), image_mode)
            except Exception:
                continue
            cells.append(
                '<td style="padding:0 8px 0 0;">'
                f'<a href="{escape_text(url)}" target="_blank" style="text-decoration:none;">'
                f'<img src="{src}" width="16" height="16" alt="{escape_text(label)}" '
                f'style="{IMG_STYLE}" />'
                "</a></td>"
            )
        if not cells:
            return ""
        return (
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
            'style="border-collapse:collapse;margin-top:8px;"><tr>'
            + "".join(cells)
            + "</tr></table>"
        )


def _wordmark_lines(name: str) -> tuple[str, str, str]:
    """Split the CAC lockup like the original signature. Other names stay on one line."""
    raw = (name or "").strip()
    if raw == "Cámara Argentina de Comercio y Servicios":
        return (
            escape_text("Cámara"),
            escape_text("Argentina de"),
            escape_text("Comercio y Servicios"),
        )
    return (escape_text(raw), "", "")


def _display_host(value: str) -> str:
    """Turn a URL or domain into a short label like cac.com.ar."""
    raw = (value or "").strip()
    raw = raw.replace("https://", "").replace("http://", "").replace("www.", "")
    return raw.rstrip("/")
