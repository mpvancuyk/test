"""Command line: python -m amacite 12345678 [more PMIDs...]"""
from __future__ import annotations

import argparse
import sys

from .ama import format_citation
from .pubmed import fetch_articles, parse_pmid


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="amacite", description="AMA citations from PubMed IDs.")
    p.add_argument("pmids", nargs="+", help="PMIDs (also accepts 'PMID: 123' or PubMed URLs)")
    p.add_argument("-f", "--format", choices=["text", "markdown", "html"], default="text")
    p.add_argument("-n", "--number", action="store_true", help="prefix with 1., 2., ...")
    args = p.parse_args(argv)

    try:
        pmids = [parse_pmid(x) for x in args.pmids]
    except ValueError as e:
        p.error(str(e))
    try:
        found = fetch_articles(pmids)
    except OSError as e:
        print(f"Error contacting PubMed: {e}", file=sys.stderr)
        return 2

    status = 0
    for i, pmid in enumerate(pmids, 1):
        art = found.get(pmid)
        if art is None:
            print(f"PMID {pmid}: not found", file=sys.stderr)
            status = 1
            continue
        line = format_citation(art, args.format)
        print(f"{i}. {line}" if args.number else line)
    return status


if __name__ == "__main__":
    sys.exit(main())
