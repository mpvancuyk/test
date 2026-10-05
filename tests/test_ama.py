import unittest

from amacite.ama import format_citation, format_pages
from amacite.pubmed import Author, parse_pmid, parse_xml

XML = """<PubmedArticleSet><PubmedArticle>
<MedlineCitation><PMID>111</PMID><Article>
<Journal><JournalIssue><Volume>323</Volume><Issue>5</Issue>
<PubDate><Year>2020</Year><Month>Feb</Month></PubDate></JournalIssue></Journal>
<ArticleTitle>Effect of <i>drug</i> on outcomes.</ArticleTitle>
<Pagination><MedlinePgn>1234-9</MedlinePgn></Pagination>
<AuthorList>
<Author><LastName>Smith</LastName><Initials>AB</Initials></Author>
<Author><LastName>Jones</LastName><Initials>C</Initials><Suffix>Jr</Suffix></Author>
<Author><CollectiveName>COVID Study Group</CollectiveName></Author>
</AuthorList></Article>
<MedlineJournalInfo><MedlineTA>JAMA</MedlineTA></MedlineJournalInfo></MedlineCitation>
<PubmedData><ArticleIdList><ArticleId IdType="doi">10.1001/jama.2020.1</ArticleId></ArticleIdList></PubmedData>
</PubmedArticle></PubmedArticleSet>"""


class Tests(unittest.TestCase):
    def test_full(self):
        a = parse_xml(XML)[0]
        self.assertEqual(
            format_citation(a),
            "Smith AB, Jones C Jr, COVID Study Group. Effect of drug on outcomes. "
            "JAMA. 2020;323(5):1234-1239. doi:10.1001/jama.2020.1",
        )
        self.assertIn("*JAMA*.", format_citation(a, "markdown"))
        self.assertIn("<i>JAMA</i>.", format_citation(a, "html"))

    def test_et_al(self):
        a = parse_xml(XML)[0]
        a.authors = [Author(last=f"A{i}", initials="X") for i in range(7)]
        self.assertTrue(format_citation(a).startswith("A0 X, A1 X, A2 X, et al. "))
        a.authors = a.authors[:6]
        self.assertNotIn("et al", format_citation(a))

    def test_ahead_of_print(self):
        a = parse_xml(XML)[0]
        a.volume = a.issue = a.pages = ""
        a.epub_year, a.epub_month, a.epub_day = "2020", "03", "04"
        self.assertIn("JAMA. Published online March 4, 2020. doi:", format_citation(a))

    def test_no_issue_and_elocation(self):
        a = parse_xml(XML)[0]
        a.issue, a.pages = "", "e123"
        self.assertIn("2020;323:e123.", format_citation(a))

    def test_pages(self):
        self.assertEqual(format_pages("123-30"), "123-130")
        self.assertEqual(format_pages("S12-S19"), "S12-S19")
        self.assertEqual(format_pages("e100-e5"), "e100-e105")
        self.assertEqual(format_pages("55"), "55")

    def test_pmid(self):
        self.assertEqual(parse_pmid("PMID: 31241231"), "31241231")
        self.assertEqual(parse_pmid("https://pubmed.ncbi.nlm.nih.gov/31241231/"), "31241231")


if __name__ == "__main__":
    unittest.main()
