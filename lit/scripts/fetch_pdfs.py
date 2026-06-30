#!/usr/bin/env python3
"""Stage 5 prep: download open-access PDFs locally for full-text reading (no Zotero cloud storage).

Resolves a PDF per paper in this order: explicit oa_pdf -> arXiv (from id/url) -> Unpaywall(DOI).
Non-OA papers (paywalled IEEE/Elsevier) simply won't download -> Stage 5 falls back to abstract cards.

Usage: python fetch_pdfs.py --selected runs/<slug>/selected.jsonl --out runs/<slug>/pdfs
"""
import argparse, json, os, re, urllib.request, urllib.parse

UA = {"User-Agent": "research-agent/0.1 (mailto:sprinter2026capstone@gmail.com)"}


def arxiv_id(r):
    for s in (r.get("url", ""), r.get("doi", ""), r.get("arxiv_id", "")):
        m = re.search(r"(\d{4}\.\d{4,5})", s or "")
        if m:
            return m.group(1)
    return ""


def unpaywall_pdf(doi):
    if not doi:
        return ""
    try:
        url = f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email=sprinter2026capstone@gmail.com"
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as resp:
            d = json.load(resp)
        loc = d.get("best_oa_location") or {}
        return loc.get("url_for_pdf") or ""
    except Exception:
        return ""


def download(url, dest):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as resp:
            data = resp.read()
        if len(data) < 1000 or not data[:5].startswith(b"%PDF") and b"%PDF" not in data[:1024]:
            return False
        open(dest, "wb").write(data)
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selected", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rows = [json.loads(l) for l in open(a.selected)]
    man = open(os.path.join(a.out, "_manifest.tsv"), "w")
    ok = 0
    for r in rows:
        n = r["n"]
        cands = []
        if r.get("oa_pdf"):
            cands.append(r["oa_pdf"])
        aid = arxiv_id(r)
        if aid:
            cands.append(f"https://arxiv.org/pdf/{aid}")
        up = unpaywall_pdf(r.get("doi", ""))
        if up:
            cands.append(up)
        dest = os.path.join(a.out, f"{n:02d}.pdf")
        got = ""
        for u in cands:
            if download(u, dest):
                got = u
                ok += 1
                break
        man.write(f"{n}\t{'OK' if got else 'MISS'}\t{dest if got else ''}\t{r['title'][:60]}\n")
        print(f"  [{n:>2}] {'OK ' if got else 'MISS'} {r['title'][:55]}")
    man.close()
    print(f"\n[pdfs] downloaded {ok}/{len(rows)} -> {a.out}")


if __name__ == "__main__":
    main()
