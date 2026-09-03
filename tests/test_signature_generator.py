"""HTML generation: optional fields, escaping, templates, no empty blocks."""

from __future__ import annotations

from signature_builder.core.models import PersonData
from signature_builder.core.signature_generator import SignatureGenerator


def test_full_person_includes_name_contact_and_company(generator: SignatureGenerator, person: PersonData) -> None:
    html = generator.render_fragment(person, image_mode="relative")
    assert "María González" in html
    assert "Analista de Soporte" in html
    assert "Tecnología" in html
    assert "Cámara Argentina de Comercio y Servicios" in html
    assert "maria.gonzalez@cac.com.ar" in html
    assert "cac.com.ar" in html
    assert "linkedin.com" in html
    assert "assets/logo-animated.gif" in html
    assert "<script" not in html.lower() or "script&gt;" in html


def test_empty_optional_fields_are_omitted(generator: SignatureGenerator) -> None:
    html = generator.render_fragment(
        PersonData(first_name="Ana", last_name="López"),
        image_mode="relative",
    )
    assert "Ana López" in html
    assert "linkedin" not in html.lower()
    assert "instagram" not in html
    assert "mailto:" not in html
    assert "tel:" not in html


def test_html_injection_is_escaped(generator: SignatureGenerator) -> None:
    html = generator.render_fragment(
        PersonData(first_name='<img src=x onerror="alert(1)">', title="Director & CEO"),
        image_mode="relative",
    )
    assert "<img src=x" not in html
    assert "&lt;img" in html
    assert "Director &amp; CEO" in html


def test_gmail_clipboard_html_uses_hosted_logo(generator: SignatureGenerator, person: PersonData) -> None:
    generator.brand.logo.public_url = "https://cdn.example.com/logo-cac.png"
    html = generator.render_fragment(person, image_mode="hosted")
    assert "https://cdn.example.com/logo-cac.png" in html
    assert "file:" not in html
    assert "C:\\" not in html
    assert "logo-animated.gif" not in html
    assert "assets/phone.png" not in html
    assert html.count("data:image") >= 4
    assert "María González" in html
    assert "linkedin.com" in html
    assert "instagram" not in html
    assert "facebook" not in html
    assert len(html) < 10_000


def test_hosted_mode_omits_logo_when_public_url_missing(generator: SignatureGenerator) -> None:
    generator.brand.logo.public_url = ""
    html = generator.render_fragment(PersonData(first_name="Ana"), image_mode="hosted")
    assert 'alt="CAC"' not in html
    assert "logo-animated.gif" not in html
    assert "file:" not in html
    assert "data:image" in html


def test_javascript_url_is_not_emitted(generator: SignatureGenerator) -> None:
    html = generator.render_fragment(
        PersonData(first_name="Juan", website="javascript:alert(1)", linkedin="javascript:alert(1)"),
        image_mode="relative",
    )
    assert "javascript:" not in html


def test_document_wraps_fragment(generator: SignatureGenerator, person: PersonData) -> None:
    doc = generator.render_document(person, image_mode="relative")
    assert "<!DOCTYPE html>" in doc
    assert 'id="signature-root"' in doc
    assert "display:flex" not in doc
    assert "grid-template" not in doc


def test_gmail_mode_ignores_instagram_even_if_filled(generator: SignatureGenerator) -> None:
    html = generator.render_fragment(
        PersonData(first_name="Ana", instagram="https://instagram.com/x", facebook="https://facebook.com/x"),
        image_mode="relative",
    )
    assert "instagram" not in html
    assert "facebook" not in html


def test_modern_and_minimal_templates_render(brand_dir, person: PersonData) -> None:
    from signature_builder.core.asset_manager import AssetManager
    from signature_builder.core.models import BrandConfig

    for name in ("modern", "minimal"):
        brand = BrandConfig(template=name)
        html = SignatureGenerator(brand, AssetManager(brand, brand_dir)).render_fragment(
            person, image_mode="relative"
        )
        assert person.full_name() in html
        assert "logo-animated.gif" in html


def test_original_template_keeps_gif_on_the_isotipo(generator: SignatureGenerator, person: PersonData) -> None:
    html = generator.render_fragment(person, image_mode="relative", template="original")
    assert "Analista de Soporte" in html
    assert "Cámara" in html
    assert "Argentina de" in html
    assert "Comercio y Servicios" in html
    assert "assets/logo-animated.gif" in html
    assert 'width="72"' in html
    assert html.find("Analista de Soporte") < html.find("logo-animated.gif")
    assert html.find("web.png") < html.find("logo-animated.gif")
    assert "display:flex" not in html


def test_original_and_corporate_put_the_logo_on_opposite_sides(
    generator: SignatureGenerator,
) -> None:
    person = PersonData(website="cac.com.ar")
    original = generator.render_fragment(person, image_mode="relative", template="original")
    corporate = generator.render_fragment(person, image_mode="relative", template="corporate")
    assert original != corporate
    assert original.find("web.png") < original.find("logo-animated.gif")
    assert corporate.find("logo-animated.gif") < corporate.find("web.png")
    assert 'width="72"' in original
    assert 'width="140"' in corporate


def test_document_records_the_selected_model(generator: SignatureGenerator) -> None:
    doc = generator.render_document(PersonData(), image_mode="relative", template="original")
    assert 'data-model="original"' in doc


def test_original_hosted_copy_still_uses_public_gif(generator: SignatureGenerator, person: PersonData) -> None:
    generator.brand.logo.public_url = "https://cdn.example.com/logo-cac.gif"
    html = generator.render_fragment(person, image_mode="hosted", template="original")
    assert "https://cdn.example.com/logo-cac.gif" in html
    assert "file:" not in html
    assert html.count("<img") >= 2
