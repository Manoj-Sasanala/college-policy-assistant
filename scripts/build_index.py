"""L3 regeneration command: C03 chunks -> local retrieval index.

Reads a C03 chunk artifact (produced by L2) and writes a deterministic
local index JSON to data/index/.

Usage:
    python scripts/build_index.py data/chunks/attendance-policy.chunks.json
    python scripts/build_index.py data/chunks/attendance-policy.chunks.json --out data/index/attendance-policy.index.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.retrieval.index_store import build_index, save_index
from app.retrieval.retriever import RetrievalError, load_chunks

DEFAULT_OUT_DIR = Path("data/index")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local L3 retrieval index from C03 chunks.")
    parser.add_argument("chunks", help="Path to a C03 chunk JSON file.")
    parser.add_argument(
        "--out",
        default=None,
        help="Output index path. Defaults to data/index/<stem>.index.json",
    )
    args = parser.parse_args(argv)

    src = Path(args.chunks)
    if not src.is_file():
        print(f"error: chunk file not found: {src}", file=sys.stderr)
        return 2

    try:
        chunks = load_chunks(src)
    except RetrievalError as exc:
        print(f"error: invalid C03 chunks: {exc}", file=sys.stderr)
        return 3

    index = build_index(chunks)

    if args.out:
        out = Path(args.out)
    else:
        out = DEFAULT_OUT_DIR / f"{src.stem}.index.json"

    save_index(index, out)
    print(f"wrote index for {len(chunks)} chunk(s) to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
