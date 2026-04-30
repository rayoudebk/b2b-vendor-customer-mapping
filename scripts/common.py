import csv
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests


USER_AGENT = "b2b-vendor-customer-mapping/0.1 (+public research; respectful crawl)"

CUSTOMER_SURFACE_TERMS = {
    "customers": 6,
    "clients": 6,
    "customer-stories": 7,
    "customer_story": 7,
    "case-studies": 7,
    "case-study": 7,
    "success-stories": 6,
    "testimonials": 6,
    "references": 5,
    "press-releases": 4,
    "press-release": 4,
    "news": 2,
    "partners": 2,
}

NOISE_NAMES = {
    "award winner",
    "calendar",
    "company",
    "ebook",
    "inflation",
    "logo",
    "partner",
    "privacy policy",
    "terms",
    "webinar",
    "whitepaper",
}

STOPWORDS = {
    "the",
    "and",
    "of",
    "for",
    "with",
    "a",
    "an",
    "in",
    "on",
    "by",
    "to",
    "from",
    "group",
    "company",
    "corporation",
    "corp",
    "inc",
    "ltd",
    "limited",
    "plc",
    "llc",
    "sa",
    "sas",
    "ag",
    "gmbh",
    "asset",
    "management",
    "bank",
    "capital",
    "financial",
    "services",
    "logo",
}


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows([{k: r.get(k, "") for k in fields} for r in rows])


def append_csv(path, row, fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in fields})


def normalize_text(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def slugify(value):
    return normalize_text(value).replace(" ", "-") or "vendor"


def ensure_url(value):
    value = (value or "").strip()
    if not value:
        return ""
    if not re.match(r"^https?://", value, flags=re.I):
        value = "https://" + value
    return value.rstrip("/")


def canonical_url(value, base=""):
    if not value:
        return ""
    url = urljoin(base, value.strip())
    url = urldefrag(url)[0]
    p = urlparse(url)
    path = re.sub(r"/+$", "", p.path) or "/"
    return p._replace(scheme=p.scheme.lower(), netloc=p.netloc.lower(), path=path, params="", query="", fragment="").geturl()


def url_basename(value):
    p = urlparse(canonical_url(value))
    name = Path(p.path).name
    return re.sub(r"\.[a-z0-9]{2,5}$", "", name, flags=re.I)


def fetch(url, timeout=15):
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
    return requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)


def surface_score(url, text=""):
    hay = normalize_text(url + " " + (text or ""))
    score = 0
    matched = []
    for term, weight in CUSTOMER_SURFACE_TERMS.items():
        norm = normalize_text(term)
        if norm in hay:
            score += weight
            matched.append(term)
    surface_type = "other"
    if any(t in matched for t in ["case-studies", "case-study", "customer-stories", "customer_story", "success-stories"]):
        surface_type = "case_study"
    elif any(t in matched for t in ["customers", "clients", "references", "testimonials"]):
        surface_type = "customer_list"
    elif any(t in matched for t in ["press-releases", "press-release", "news"]):
        surface_type = "news_or_press"
    elif "partners" in matched:
        surface_type = "partner_or_ecosystem"
    return score, surface_type, matched


def name_tokens(value):
    return [t for t in normalize_text(value).split() if len(t) >= 3 and t not in STOPWORDS]


def name_supported(customer, texts):
    cn = normalize_text(customer)
    hay = normalize_text(" ".join(t for t in texts if t))
    if not cn:
        return False, "empty_customer"
    if cn in NOISE_NAMES:
        return False, "known_noise_name"
    if cn in hay:
        return True, "exact_normalized"
    toks = name_tokens(customer)
    if len(toks) == 1:
        return toks[0] in hay.split(), "single_token"
    hits = [t for t in toks if t in hay]
    ratio = len(hits) / len(toks) if toks else 0
    ok = (len(toks) == 2 and len(hits) == 2) or (len(toks) >= 3 and ratio >= 0.75 and len(hits) >= 2)
    return ok, f"token_{len(hits)}_of_{len(toks)}" + (":" + "|".join(hits) if hits else "")


def clean_candidate_name(value, vendor_name=""):
    value = re.sub(r"\s+", " ", value or "").strip(" -|:•\t\r\n")
    value = re.sub(r"\b(case study|customer story|client story|testimonial|success story)\b", "", value, flags=re.I).strip(" -|:")
    if vendor_name:
        value = re.sub(re.escape(vendor_name), "", value, flags=re.I).strip(" -|:")
    value = re.sub(r"\s+", " ", value).strip()
    norm = normalize_text(value)
    if len(value) < 2 or len(value) > 90:
        return ""
    if norm in NOISE_NAMES:
        return ""
    if len(value.split()) > 8:
        return ""
    if re.search(r"[.!?]$", value):
        return ""
    return value


def infer_name_from_slug(url):
    raw = url_basename(url).replace("-", " ").replace("_", " ")
    raw = re.sub(r"\b(case|study|customer|client|story|success|press|release|news)\b", " ", raw, flags=re.I)
    return re.sub(r"\s+", " ", raw).strip().title()


def extract_json_array(text):
    text = (text or "").strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else []
    except Exception:
        pass
    match = re.search(r"\[[\s\S]*\]", text)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, list) else []
    except Exception:
        return []
