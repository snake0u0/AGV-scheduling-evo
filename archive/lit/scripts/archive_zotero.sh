#!/usr/bin/env bash
# Stage 4: add selected papers to a Zotero collection via zotero-cli (metadata + linked URL, no cloud storage).
# Creds are read from ~/.claude.json (mcpServers.zotero.env) so no secret is passed on the command line.
# Usage: archive_zotero.sh <selected.jsonl> <collection_key> <archive_log.md>
set -u
export PATH="$HOME/.local/bin:$PATH"
SEL="$1"; COLL="$2"; LOG="$3"

eval "$(python3 - <<'PY'
import json, os
d = json.load(open(os.path.expanduser('~/.claude.json')))
env = ((d.get('mcpServers') or {}).get('zotero') or {}).get('env', {})
for k in ('ZOTERO_LOCAL', 'ZOTERO_LIBRARY_TYPE', 'ZOTERO_LIBRARY_ID', 'ZOTERO_API_KEY'):
    print(f"export {k}={env.get(k,'')!r}")
PY
)"
[ -n "${ZOTERO_API_KEY:-}" ] || { echo "no creds in ~/.claude.json"; exit 1; }
echo "library=$ZOTERO_LIBRARY_ID collection=$COLL"

{ echo "# archive_log — collection $COLL ($(TZ=Asia/Seoul date +%F))"; echo;
  echo "attach-mode: linked_url (no cloud storage). PDFs for full-text read locally in Stage 5."; echo;
  echo "| # | status | id | title |"; echo "|--|--------|----|-------|"; } > "$LOG"

python3 - "$SEL" <<'PY' > /tmp/_addlist.tsv
import json, sys
for r in (json.loads(l) for l in open(sys.argv[1])):
    kind, ident = ("doi", r["doi"]) if r.get("doi") else ("url", r.get("url",""))
    print(f'{r["n"]}\t{kind}\t{ident}\t{r["title"][:65].replace(chr(124),"/")}')
PY

ok=0; fail=0
while IFS=$'\t' read -r n kind ident title; do
  [ -z "$ident" ] && { echo "| $n | SKIP(no id) |  | $title |" >> "$LOG"; continue; }
  out=$(timeout 40 zotero-cli add "$kind" "$ident" --collections "$COLL" --tags agv-llm-heuristic --attach-mode linked_url 2>&1)
  if echo "$out" | grep -qiE 'error|fail|traceback|exception|quota|denied|invalid|not found'; then
    st=FAIL; fail=$((fail+1)); echo "  [$n] FAIL $ident :: $(echo "$out" | tail -1)"
  else
    st=OK; ok=$((ok+1)); echo "  [$n] OK   $ident"
  fi
  echo "| $n | $st | $ident | $title |" >> "$LOG"
done < /tmp/_addlist.tsv

TOT=$(curl -s -D - -o /dev/null -H "Zotero-API-Key: $ZOTERO_API_KEY" \
  "https://api.zotero.org/users/$ZOTERO_LIBRARY_ID/collections/$COLL/items/top?limit=1" \
  | grep -i 'total-results' | tr -dc '0-9')
echo; echo "=== added OK=$ok FAIL=$fail | collection top-items now: $TOT ==="
{ echo; echo "**summary:** OK=$ok FAIL=$fail, collection top-items=$TOT"; } >> "$LOG"
