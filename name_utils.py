# name_utils.py
import csv, re, numpy as np
from functools import lru_cache
from collections import defaultdict
from rapidfuzz import process, fuzz

# ── helpers ────────────────────────────────────────────────────────────────
def expand_initial_surname(token: str):
    # “COK I”  →  “I COK”;   “L COK” → “L COK” (unchanged)
    if re.match(r"^[A-Z]{2,}\s[A-Z]$", token):
        last, initial = token.split()
        return f"{initial} {last}"
    if re.match(r"^[A-Z]\s[A-Z]{2,}$", token):
        initial, last = token.split()
        return f"{initial} {last}"
    return token

def canonize_score_tokens(tokens):
    if len(tokens) == 6:
        return tokens
    if len(tokens) == 8:
        t1, s1, r1, t2, s2, r2 = (
            tokens[0] + "/" + tokens[1],
            tokens[2], tokens[3],
            tokens[4] + "/" + tokens[5],
            tokens[6], tokens[7],
        )
        return [t1, s1, r1, t2, s2, r2]
        # NEW: 4‑token  [name1, s1, name2, s2]  (no game‑points shown)
    if len(tokens) == 4:
        team1, s1, team2, s2 = tokens
        r1 = r2 = "0"          # we don’t have in‑game points, fill with “0”
        return [team1, s1, r1, team2, s2, r2]

    return None

def extract_name_spans(canon_tokens):
    return [canon_tokens[0], canon_tokens[3]]

def raw_token_lists_from_data(all_data):
    out, repl = [], {"O": "0"}
    for ok, idx, result in all_data:
        if not ok or result is None or (isinstance(result, str) and "OPTIM" in result):
            continue
        det = result[0]
        if det is None:
            continue
        toks = [r[1][0] for r in det]
        for i, t in enumerate(toks):
            if t in repl: toks[i] = repl[t]
            toks[i] = toks[i].replace(".", "")
        out.append((idx, toks))
    return out

def load_reference_names(csv_path="./data/player_list.csv"):
    refs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if row:
                refs.append(" ".join(row[0].upper().split()))
    return refs

# ── surname index (global, built once) ─────────────────────────────────────
_reference_names = tuple(load_reference_names())  # used by cached matcher

surname_index = defaultdict(list)   # surname → list(full names)
for full in _reference_names:
    surname_index[full.split()[-1]].append(full)

# ── main matcher ───────────────────────────────────────────────────────────
@lru_cache(maxsize=None)
def cached_match_name(span: str) -> str | None:
    """
    Return best‑matched full name (or 'A / B' for doubles) or None.
    """
    query = expand_initial_surname(span.replace("-", " ").upper().strip())
    query = " ".join(query.split())

    # ——— doubles ————————————————————————————
    if "/" in query:
        parts, matched = [p.strip() for p in query.split("/")], []
        for part in parts:
            hit = cached_match_name(part)    # recurse on singles logic
            if hit is None:
                return None
            matched.append(hit)
        return " / ".join(matched)

    # ——— singles  (exact → reversed → unique surname → fuzzy) ————————
    if query in _reference_names:
        return query

    tokens = query.split()
    if len(tokens) > 1:
        rev = " ".join(tokens[::-1])
        if rev in _reference_names:
            return rev

    if len(tokens) == 1:
        surname = tokens[0]
        hits = surname_index.get(surname, [])
        if len(hits) == 1:              # unique → return directly
            return hits[0]

        # NEW: when multiple players share the surname,
        #      pick the one with highest fuzzy score
        best, score, _ = process.extractOne(surname, hits or _reference_names,
                                            scorer=fuzz.token_set_ratio)
        if score >= 90:                 # very strict: need perfect surname match
            return best


    match, score, _ = process.extractOne(query, _reference_names, scorer=fuzz.token_set_ratio) or (None, 0, None)
    return match if score >= 75 else None
