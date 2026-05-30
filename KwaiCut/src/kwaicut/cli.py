"""Command line interface for KwaiCut.

Provides a few operational entry points without forcing the heavy desktop/AI
dependencies to be installed:

    kwaicut version
    kwaicut initdb
    kwaicut serve            # run the FastAPI backend
    kwaicut captions IN.wav OUT.srt
"""

from __future__ import annotations

import argparse
import sys

from kwaicut import __version__
from kwaicut.common.logging_config import configure_logging, get_logger

logger = get_logger(__name__)


def _cmd_version(_: argparse.Namespace) -> int:
    print(f"KwaiCut {__version__}")
    return 0


def _cmd_initdb(_: argparse.Namespace) -> int:
    from kwaicut.db.base import init_db

    init_db()
    print("Database initialised.")
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:  # pragma: no cover - launches server
    import uvicorn

    uvicorn.run("kwaicut.backend.app:app", host=args.host, port=args.port, reload=args.reload)
    return 0


def _cmd_captions(args: argparse.Namespace) -> int:
    from kwaicut.ai.captions import AutoCaptions

    transcript = AutoCaptions().generate(args.input, args.output, language=args.language)
    print(f"Wrote {len(transcript.segments)} caption segments to {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kwaicut", description="KwaiCut CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("version", help="print the version").set_defaults(func=_cmd_version)
    sub.add_parser("initdb", help="create database tables").set_defaults(func=_cmd_initdb)

    serve = sub.add_parser("serve", help="run the backend API")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true")
    serve.set_defaults(func=_cmd_serve)

    captions = sub.add_parser("captions", help="generate an SRT from audio")
    captions.add_argument("input")
    captions.add_argument("output")
    captions.add_argument("--language", default=None)
    captions.set_defaults(func=_cmd_captions)

    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
