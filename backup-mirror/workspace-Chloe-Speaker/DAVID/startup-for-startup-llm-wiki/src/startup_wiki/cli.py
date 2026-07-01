from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipeline import Pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="startup-wiki",
        description="Transcript-to-wiki pipeline for Startup for Startup transcripts.",
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project workspace root.")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_input_command(name: str, help_text: str) -> argparse.ArgumentParser:
        cmd = sub.add_parser(name, help=help_text)
        cmd.add_argument("--input", type=Path, required=True, help="Directory containing raw transcript .md/.txt files.")
        return cmd

    add_input_command("ingest", "Copy transcript sources into the workspace inbox.")
    sub.add_parser("normalize", help="Normalize staged transcripts.")
    sub.add_parser("chunk", help="Chunk normalized transcripts.")
    sub.add_parser("index", help="Build transcript indexes.")
    sub.add_parser("wiki", help="Generate wiki pages.")
    sub.add_parser("export", help="Export the wiki into an Obsidian-ready vault.")
    sub.add_parser("report", help="Write QA and run reports.")
    add_input_command("run", "Run the full pipeline end-to-end.")
    return parser


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    argv = _normalize_argv(argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    pipeline = Pipeline(args.root)

    if args.command == "ingest":
        stats = pipeline.ingest(args.input)
        print(f"ingested={stats.staged} discovered={stats.discovered} skipped={stats.skipped}")
    elif args.command == "normalize":
        items = pipeline.normalize()
        print(f"normalized={len(items)}")
    elif args.command == "chunk":
        items = pipeline.chunk()
        print(f"chunks={len(items)}")
    elif args.command == "index":
        outputs = pipeline.build_indexes()
        print(f"indexes={len(outputs)}")
    elif args.command == "wiki":
        items = pipeline.generate_wiki()
        print(f"wiki_pages={len(items)}")
    elif args.command == "export":
        items = pipeline.export_obsidian()
        print(f"exported={len(items)}")
    elif args.command == "report":
        outputs = pipeline.write_reports()
        print(f"reports={', '.join(f'{key}={value}' for key, value in outputs.items())}")
    elif args.command == "run":
        result = pipeline.run_all(args.input)
        print(
            "run_complete "
            f"ingested={result['ingest'].staged} "
            f"normalized={result['normalized']} "
            f"chunks={result['chunks']} "
            f"wiki_pages={result['wiki_pages']} "
            f"exported={result['exported']}"
        )
    else:
        parser.error("Unknown command")


def _normalize_argv(argv: list[str]) -> list[str]:
    if "--root" not in argv:
        return argv
    root_index = argv.index("--root")
    if root_index <= 0:
        return argv
    if root_index + 1 >= len(argv):
        return argv
    root_pair = argv[root_index : root_index + 2]
    remaining = argv[:root_index] + argv[root_index + 2 :]
    return root_pair + remaining
