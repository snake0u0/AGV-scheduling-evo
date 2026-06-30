#!/usr/bin/env python3
"""Stage 2 collector (MVP): OpenAlex multi-query search + seed-paper reference expansion + dedup.

Stdlib only (urllib/json), mirrors AutoResearchClaw's dependency-free approach.
OpenAlex already indexes arXiv + journals + proceedings and gives citation counts +
abstracts, so it is the single lean discovery source for v1. arXiv/Scholar stay manual.

Usage:
  python collect.py --queries runs/<slug>/queries.txt --seed-doi 10.48550/arxiv.2603.27628 \
      --year-min 2016 --out runs/<slug>/candidates.jsonl --email you@example.com
"""
import argparse, json, re, sys, time, urllib.parse, urllib.request

API = "https://api.openalex.org/works"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "research-agent/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.load(r)
    except Exception as e:
        print(f"  ! fetch failed: {e}", file=sys.stderr)
        return None


def recon_abstract(inv):
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))[:1200]


def norm_title(t):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", (t or "").lower())).strip()


def to_candidate(w, source):
    if not w:
        return None
    doi = (w.get("doi") or "").replace("https://doi.org/", "")
    src_loc = w.get("primary_location") or {}
    venue = ((src_loc.get("source") or {}) or {}).get("display_name") or ""
    oa = (w.get("best_oa_location") or {}) or {}
    arxiv_id = ""
    for loc in (w.get("locations") or []):
        lp = (loc.get("landing_page_url") or "")
        m = re.search(r"arxiv\.org/abs/([\d.]+)", lp)
        if m:
            arxiv_id = m.group(1)
            break
    title = w.get("title") or w.get("display_name") or ""
    return {
        "title": title,
        "authors": [a["author"]["display_name"] for a in (w.get("authorships") or [])[:8]],
        "year": w.get("publication_year") or 0,
        "venue": venue,
        "abstract": recon_abstract(w.get("abstract_inverted_index")),
        "citation_count": w.get("cited_by_count") or 0,
        "doi": doi,
        "arxiv_id": arxiv_id,
        "url": (w.get("doi") or src_loc.get("landing_page_url") or w.get("id") or ""),
        "oa_pdf": oa.get("pdf_url") or "",
        "source": source,
    }


def search(query, year_min, email, per_page=25):
    flt = f"from_publication_date:{year_min}-01-01"
    qs = urllib.parse.urlencode({"search": query, "per_page": per_page, "filter": flt, "mailto": email})
    d = get(f"{API}?{qs}")
    return [to_candidate(w, "openalex:query") for w in (d or {}).get("results", [])]


def expand_seed(doi, email, cap=60):
    d = get(f"{API}/doi:{urllib.parse.quote(doi)}?mailto={email}")
    if not d:
        print("  ! seed DOI not found on OpenAlex", file=sys.stderr)
        return []
    refs = d.get("referenced_works") or []
    print(f"  seed '{(d.get('title') or '')[:50]}' -> {len(refs)} references", file=sys.stderr)
    out = [to_candidate(d, "seed")]
    for wid in refs[:cap]:
        wid = wid.rstrip("/").split("/")[-1]
        w = get(f"{API}/{wid}?mailto={email}")
        out.append(to_candidate(w, "seed:ref"))
        time.sleep(0.12)
    return out


def dedupe(cands):
    by_id, order = {}, []
    for c in cands:
        if not c or not c["title"]:
            continue
        key = ("doi:" + c["doi"].lower()) if c["doi"] else ("arx:" + c["arxiv_id"]) if c["arxiv_id"] else ("ti:" + norm_title(c["title"]))
        if key in by_id:
            if c["citation_count"] > by_id[key]["citation_count"]:
                # keep richer record but remember it was multi-sourced
                c["source"] = by_id[key]["source"] + "+" + c["source"]
                by_id[key] = c
            continue
        by_id[key] = c
        order.append(key)
    return [by_id[k] for k in order]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", required=True)
    ap.add_argument("--seed-doi", default="")
    ap.add_argument("--year-min", type=int, default=2016)
    ap.add_argument("--out", required=True)
    ap.add_argument("--email", default="sprinter2026capstone@gmail.com")
    ap.add_argument("--per-query", type=int, default=25)
    a = ap.parse_args()

    queries = [ln.strip() for ln in open(a.queries) if ln.strip() and not ln.startswith("#")]
    all_c = []
    if a.seed_doi:
        print("[seed expansion]", file=sys.stderr)
        all_c += expand_seed(a.seed_doi, a.email)
    print(f"[searching {len(queries)} queries]", file=sys.stderr)
    for q in queries:
        hits = search(q, a.year_min, a.email, a.per_query)
        print(f"  '{q[:45]}' -> {len(hits)}", file=sys.stderr)
        all_c += hits
        time.sleep(0.2)

    deduped = dedupe(all_c)
    deduped.sort(key=lambda c: (c["citation_count"], c["year"]), reverse=True)
    with open(a.out, "w") as f:
        for c in deduped:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"\n[done] raw={len(all_c)} deduped={len(deduped)} -> {a.out}")
    yrs = {}
    for c in deduped:
        yrs[c["year"]] = yrs.get(c["year"], 0) + 1
    print("by year:", dict(sorted(yrs.items())))
    print("top 8 by citations:")
    for c in deduped[:8]:
        print(f"  {c['year']} c={c['citation_count']:>5} | {c['title'][:70]}")


if __name__ == "__main__":
    main()
