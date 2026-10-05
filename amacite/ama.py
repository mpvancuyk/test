"""Format an Article as an AMA Manual of Style (11th ed.) journal reference."""
from __future__ import annotations

import html
import re

from .pubmed import Article, Author

MONTHS = [
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
]
_MONTH_ABBR = {m[:3]: m for m in MONTHS}
MAX_AUTHORS = 6  # more than 6 -> list first 3 then "et al"


def _author(a: Author) -> str:
    if a.collective:
        return a.collective
    name = f"{a.last} {a.initials}".strip()
    return f"{name} {a.suffix}".strip() if a.suffix else name


def format_authors(authors: list[Author]) -> str:
    names = [_author(a) for a in authors if a.last or a.collective]
    if len(names) > MAX_AUTHORS:
        return ", ".join(names[:3]) + ", et al"
    return ", ".join(names)


def format_pages(pages: str) -> str:
    """Expand PubMed's abbreviated ranges: '1234-9' -> '1234-1239'."""
    m = re.fullmatch(r"([A-Za-z]*)(\d+)\s*-\s*([A-Za-z]*)(\d+)", pages.strip())
    if not m:
        return pages.strip()
    p1, s, p2, e = m.groups()
    if len(e) < len(s):
        e = s[: len(s) - len(e)] + e
    return f"{p1}{s}-{p2 or p1}{e}"


def _title(title: str) -> str:
    title = title.strip()
    if title.startswith("[") and title.endswith("]."):  # PubMed translated-title marker
        title = title[1:-2]
    elif title.startswith("[") and title.endswith("]"):
        title = title[1:-1]
    return title.rstrip(". ")


def _online_date(a: Article) -> str:
    y, mo, d = a.epub_year, a.epub_month, a.epub_day
    if not y:
        y, mo, d = a.year, a.month, a.day
    if mo.isdigit() and 1 <= int(mo) <= 12:
        mo = MONTHS[int(mo) - 1]
    else:
        mo = _MONTH_ABBR.get(mo[:3], mo)
    parts = [p for p in (mo, str(int(d)) if d.isdigit() else "") if p]
    return (" ".join(parts) + ("," if d and mo else "") + f" {y}").strip()


def format_citation(a: Article, style: str = "text") -> str:
    """Return the AMA citation. style: 'text', 'markdown' (*italic*) or 'html' (<i>)."""
    journal = a.journal.replace(".", "")
    if style == "markdown":
        journal = f"*{journal}*"
    elif style == "html":
        journal = f"<i>{html.escape(journal)}</i>"

    title = _title(a.title)
    if style == "html":
        title = html.escape(title)

    parts = []
    authors = format_authors(a.authors)
    if authors:
        parts.append(authors.rstrip(".") + ".")
    parts.append(title + ".")

    if a.volume:
        loc = f"{a.year};{a.volume}"
        if a.issue:
            issue = re.sub(r"^suppl", "suppl", a.issue, flags=re.I)
            loc += f"({issue})"
        if a.pages:
            loc += f":{format_pages(a.pages)}"
        parts.append(f"{journal}. {loc}.")
    elif a.pages and a.year:  # article number without a volume
        parts.append(f"{journal}. {a.year}:{format_pages(a.pages)}.")
    else:  # ahead of print
        parts.append(f"{journal}. Published online {_online_date(a)}.")

    if a.doi:
        parts.append(f"doi:{html.escape(a.doi) if style == 'html' else a.doi}")
    return " ".join(parts)
