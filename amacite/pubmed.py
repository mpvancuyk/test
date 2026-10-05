"""Fetch and parse article metadata from NCBI PubMed (E-utilities)."""
from __future__ import annotations

import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


@dataclass
class Author:
    last: str = ""
    initials: str = ""
    suffix: str = ""
    collective: str = ""


@dataclass
class Article:
    pmid: str
    title: str = ""
    authors: list[Author] = field(default_factory=list)
    journal: str = ""
    year: str = ""
    month: str = ""
    day: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    doi: str = ""
    epub_year: str = ""
    epub_month: str = ""
    epub_day: str = ""


def parse_pmid(text: str) -> str:
    """Extract a PMID from '123', 'PMID: 123' or a pubmed.ncbi.nlm.nih.gov URL."""
    m = re.search(r"(?<!\d)(\d{1,9})(?!\d)", text.strip())
    if not m:
        raise ValueError(f"Not a valid PMID: {text!r}")
    return m.group(1)


def _text(el: ET.Element | None) -> str:
    # itertext keeps text inside inline markup such as <i> and <sub>.
    return "".join(el.itertext()).strip() if el is not None else ""


def parse_xml(xml: str | bytes) -> list[Article]:
    root = ET.fromstring(xml)
    articles = []
    for pa in root.iter("PubmedArticle"):
        cit = pa.find("MedlineCitation")
        art = cit.find("Article")
        a = Article(pmid=_text(cit.find("PMID")))
        a.title = _text(art.find("ArticleTitle"))

        for au in art.findall("AuthorList/Author"):
            a.authors.append(
                Author(
                    last=_text(au.find("LastName")),
                    initials=_text(au.find("Initials")),
                    suffix=_text(au.find("Suffix")),
                    collective=_text(au.find("CollectiveName")),
                )
            )

        info = cit.find("MedlineJournalInfo/MedlineTA")
        a.journal = (
            _text(info)
            or _text(art.find("Journal/ISOAbbreviation")).replace(".", "")
            or _text(art.find("Journal/Title"))
        )

        ji = art.find("Journal/JournalIssue")
        a.volume = _text(ji.find("Volume"))
        a.issue = _text(ji.find("Issue"))
        pd = ji.find("PubDate")
        a.year = _text(pd.find("Year"))
        a.month = _text(pd.find("Month"))
        a.day = _text(pd.find("Day"))
        if not a.year:  # e.g. <MedlineDate>2019 Jan-Feb</MedlineDate>
            m = re.search(r"\d{4}", _text(pd.find("MedlineDate")))
            a.year = m.group(0) if m else ""

        a.pages = _text(art.find("Pagination/MedlinePgn"))
        if not a.pages:  # online-only journals use an article number
            for e in art.findall("ELocationID"):
                if e.get("EIdType") == "pii" and e.get("ValidYN", "Y") == "Y":
                    a.pages = _text(e)

        ed = art.find("ArticleDate")
        if ed is not None:
            a.epub_year = _text(ed.find("Year"))
            a.epub_month = _text(ed.find("Month"))
            a.epub_day = _text(ed.find("Day"))

        for i in pa.findall("PubmedData/ArticleIdList/ArticleId"):
            if i.get("IdType") == "doi":
                a.doi = _text(i)
        if not a.doi:
            for e in art.findall("ELocationID"):
                if e.get("EIdType") == "doi":
                    a.doi = _text(e)
        articles.append(a)
    return articles


def fetch_articles(pmids: list[str], timeout: float = 30) -> dict[str, Article]:
    """Fetch articles from PubMed. Returns {pmid: Article}; missing PMIDs are absent."""
    if not pmids:
        return {}
    data = urllib.parse.urlencode(
        {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}
    ).encode()
    req = urllib.request.Request(EFETCH_URL, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        xml = resp.read()
    return {a.pmid: a for a in parse_xml(xml)}
