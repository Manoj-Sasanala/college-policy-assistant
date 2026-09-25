"""L2 regeneration command: C01 source record(s) -> C03 chunk artifact.

Reads one or more C01 JSON files (the L1 source record, or the checked-in
C01 fixture when L1 output is unavailable) and writes deterministic C03
chunk records to data/chunks/.

Usage:
    python scripts/build_chunks.py data/fixtures/c01_attendance_policy.json
    python scripts/build_chunks.py data/fixtures/c01_attendance_policy.json --out data/chunks/attendance-policy.chunks.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.chunking.chunker import chunk_source
from app.ingestion.source_validator import SourceValidationError, validate_source

DEFAULT_OUT_DIR = Path("data/chunks")


def _load_record(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_chunks(out_path: Path, chunks: list[dict]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(chunks, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build C03 chunk artifacts from C01 records.")
    parser.add_argument("source", help="Path to a C01 JSON record file.")
    parser.add_argument(
        "--out",
        default=None,
        help="Output chunk file path. Defaults to data/chunks/<document_id>.chunks.json",
    )
    args = parser.parse_args(argv)

    src_path = Path(args.source)
    if not src_path.is_file():
        print(f"error: source file not found: {src_path}", file=sys.stderr)
        return 2

    try:
        record = validate_source(_load_record(src_path))
    except SourceValidationError as exc:
        print(f"error: invalid C01 record: {exc}", file=sys.stderr)
        return 3

    chunks = chunk_source(record)

    if args.out:
        out_path = Path(args.out)
    else:
        out_path = DEFAULT_OUT_DIR / f"{record['document_id']}.chunks.json"

    _write_chunks(out_path, chunks)
    print(f"wrote {len(chunks)} chunk(s) to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())