"""Entry point: GUI by default, --build-assets for the one-time GIF pipeline."""

from __future__ import annotations

import argparse
import logging
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="signature-builder")
    parser.add_argument(
        "--build-assets",
        action="store_true",
        help="Generar el GIF del logo y los iconos (proceso A, una sola vez)",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Abrir el firmador en el navegador (mismo HTML que el de escritorio)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host del firmador web")
    parser.add_argument("--port", type=int, default=8765, help="Puerto del firmador web")
    args = parser.parse_args(argv)

    from signature_builder.logging_setup import configure_logging

    configure_logging(logging.INFO)

    if args.build_assets:
        from signature_builder.tools.build_assets import build_brand_assets

        build_brand_assets()
        return 0

    if args.web:
        from signature_builder.web.server import serve

        serve(host=args.host, port=args.port)
        return 0

    from signature_builder.ui.main_window import run

    return run()


if __name__ == "__main__":
    sys.exit(main())
