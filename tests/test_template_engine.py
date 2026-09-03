"""Template engine if-blocks and token replacement."""

from signature_builder.core.template_engine import load_template, render_template


def test_if_block_omits_empty_and_keeps_filled() -> None:
    template = "A{{#if name}}{{name}}{{/if}}B{{#if title}}X{{/if}}"
    assert render_template(template, {"name": "Ana", "title": ""}) == "AAnaB"
    assert render_template(template, {"name": "", "title": "Cargo"}) == "ABX"


def test_corporate_template_exists() -> None:
    html = load_template("corporate")
    assert "{{logo_block}}" in html
    assert "display:flex" not in html
    assert "<script" not in html


def test_original_template_exists() -> None:
    html = load_template("original")
    assert "{{logo_block}}" in html
    assert "{{company_line1}}" in html
    assert "display:flex" not in html
