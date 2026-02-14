import time
import requests
import xml.etree.ElementTree as ET

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
RATE_LIMIT_INTERVAL = 8.00  # ~3 req/sec without API key


def search_pubmed(query: str, max_results: int = 100) -> list[str]:
    """Search PubMed and return a list of PMIDs."""
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
    }
    resp = requests.get(f"{BASE_URL}/esearch.fcgi", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("esearchresult", {}).get("idlist", [])


def fetch_articles(pmid_list: list[str], batch_size: int = 50) -> list[dict]:
    """Fetch article details for a list of PMIDs using efetch."""
    articles = []
    for i in range(0, len(pmid_list), batch_size):
        batch = pmid_list[i : i + batch_size]
        params = {
            "db": "pubmed",
            "id": ",".join(batch),
            "retmode": "xml",
        }
        time.sleep(RATE_LIMIT_INTERVAL)
        resp = requests.get(f"{BASE_URL}/efetch.fcgi", params=params, timeout=60)
        resp.raise_for_status()
        articles.extend(_parse_articles_xml(resp.text))
    return articles


def _parse_articles_xml(xml_text: str) -> list[dict]:
    """Parse PubMed XML response into structured article dicts."""
    root = ET.fromstring(xml_text)
    articles = []
    for article_elem in root.findall(".//PubmedArticle"):
        article = _parse_single_article(article_elem)
        if article and article["authors"]:
            articles.append(article)
    return articles


def _parse_single_article(elem) -> dict | None:
    """Parse a single PubmedArticle element."""
    medline = elem.find("MedlineCitation")
    if medline is None:
        return None

    pmid_elem = medline.find("PMID")
    pmid = pmid_elem.text if pmid_elem is not None else ""

    article_elem = medline.find("Article")
    if article_elem is None:
        return None

    title_elem = article_elem.find("ArticleTitle")
    title = title_elem.text if title_elem is not None else ""

    journal_elem = article_elem.find("Journal/Title")
    journal = journal_elem.text if journal_elem is not None else ""

    year = ""
    year_elem = article_elem.find("Journal/JournalIssue/PubDate/Year")
    if year_elem is not None:
        year = year_elem.text
    else:
        medline_date = article_elem.find("Journal/JournalIssue/PubDate/MedlineDate")
        if medline_date is not None and medline_date.text:
            year = medline_date.text[:4]

    authors = []
    author_list = article_elem.find("AuthorList")
    if author_list is not None:
        for author_elem in author_list.findall("Author"):
            last = author_elem.find("LastName")
            fore = author_elem.find("ForeName")
            if last is None:
                continue
            last_name = last.text or ""
            first_name = fore.text if fore is not None else ""
            affiliation = ""
            aff_elem = author_elem.find("AffiliationInfo/Affiliation")
            if aff_elem is not None:
                affiliation = aff_elem.text or ""
            authors.append({
                "last_name": last_name,
                "first_name": first_name,
                "affiliation": affiliation,
            })

    return {
        "pmid": pmid,
        "title": title,
        "authors": authors,
        "year": year,
        "journal": journal,
    }
