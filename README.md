# amacite

Generate AMA Manual of Style (11th ed.) journal citations from PubMed IDs. Python 3.9+, no dependencies.

```
python -m amacite 32091512 31241231          # plain text
python -m amacite -f markdown -n 32091512    # *journal* in italics, numbered
python -m amacite -f html "PMID: 32091512"   # <i>journal</i>; URLs also accepted
```

Output looks like:
`Smith AB, Jones CD, Lee E. Title in sentence case. JAMA. 2020;323(5):1234-1239. doi:10.1001/jama.2020.1234`

Rules applied: up to 6 authors listed, otherwise first 3 + "et al"; `Surname AB` names (suffix e.g. `Jr`);
NLM journal abbreviation without periods; expanded page ranges; `Published online Month D, Year.`
for ahead-of-print articles; DOI as `doi:`.

Library use: `from amacite import fetch_articles, format_citation`.
Tests: `python -m unittest discover -s tests`. Data comes from NCBI E-utilities (needs access to eutils.ncbi.nlm.nih.gov).
