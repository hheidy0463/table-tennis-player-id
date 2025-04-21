import csv, re, numpy as np
from functools import lru_cache
from collections import defaultdict
from rapidfuzz import process, fuzz

# helpers 

def _split_glued(token: str) -> str:
    # uppercase surname followed by capital‑initial given name
    m = re.match(r"^([A-Z]+)([A-Z][a-z].*)$", token)
    if m:
        return f"{m.group(1)} {m.group(2)}"
    return token

def expand_initial_surname(token: str):
    token = _split_glued(token)         

    # example: “COK I”  →  “I COK”;   “L COK” → “L COK” 
    if re.match(r"^[A-Z]{2,}\s[A-Z]$", token):
        last, initial = token.split()
        return f"{initial} {last}"
    if re.match(r"^[A-Z]\s[A-Z]{2,}$", token):
        initial, last = token.split()
        return f"{initial} {last}"
    return token
import re

def canonize_score_tokens(tokens):
    """
    Return [team1,s1,r1,team2,s2,r2] or None.
    Handles 2/3/4/6/8 tokens, and any other length by sliding
    a 4/6/8 window.  Strips stray “-” tokens automatically.
    """
    # 1) Clean & drop empties
    t = [re.sub(r'[^A-Za-z0-9/\- ]','', tok).strip() for tok in tokens if tok.strip()]
    # 1a) drop lone hyphens
    t = [tok for tok in t if tok != '-']
    L = len(t)

    # 2‑token: just two names → [n1,0,0,n2,0,0]
    if L == 2 and all(not x.isdigit() for x in t):
        return [t[0], "0", "0", t[1], "0", "0"]

    # 3‑token: [team1,s1,team2] → [team1,s1,0,team2,0,0]
    if L == 3 and t[1].isdigit() and not t[0].isdigit() and not t[2].isdigit():
        return [t[0], t[1], "0", t[2], "0", "0"]

    # If we’re not in one of our “easy” lengths, slide a window
    if L not in (2,3,4,6,8):
        for window in (8, 6, 4):
            for i in range(L - window + 1):
                sub = t[i:i+window]
                canon = canonize_score_tokens(sub)
                if canon:
                    return canon
        return None

    # 4‑token: [team1,s1,team2,s2]
    if L == 4 and t[1].isdigit() and t[3].isdigit():
        return [t[0], t[1], "0", t[2], t[3], "0"]

    # 6‑token: three sub‑cases
    if L == 6:
        # a) score‑first: [s1,team1,r1,team2,s2,r2]
        if t[0].isdigit() and t[2].isdigit() and t[4].isdigit():
            return [t[1], t[0], t[2], t[3], t[4], t[5]]
        # b) “surname given” before score
        if (
            t[2].isdigit() and t[5].isdigit()
            and " " in t[0] and " " in t[3]
        ):
            return [t[0], t[2], "0", t[3], t[5], "0"]
        # c) generic [team1,s1,r1,team2,s2,r2]
        if t[1].isdigit() and t[4].isdigit():
            return t[:]

    # 8‑token doubles: [n0,n1,s1,r1,n2,n3,s2,r2]
    if L == 8 and t[2].isdigit() and t[5].isdigit():
        return [
            f"{t[0]}/{t[1]}", t[2], t[3],
            f"{t[4]}/{t[5]}", t[6], t[7]
        ]

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

# surname index 
_reference_names = tuple(load_reference_names())  # used by cached matcher

surname_index = defaultdict(list)   # surname → list(full names)
for full in _reference_names:
    surname_index[full.split()[-1]].append(full)

# main matcher 
@lru_cache(maxsize=None)
def cached_match_name(span: str) -> str | None:
    """
    Return best‑matched full name (or 'A / B' for doubles) or None.
    """
    query = expand_initial_surname(span.replace("-", " ").upper().strip())
    query = " ".join(query.split())

    # doubles 
    if "/" in query:
        parts, matched = [p.strip() for p in query.split("/")], []
        for part in parts:
            hit = cached_match_name(part)    # recurse on singles logic
            if hit is None:
                return None
            matched.append(hit)
        return " / ".join(matched)

    # singles  (exact → reversed → unique surname → fuzzy) 
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

        # when multiple players share the surname, pick the one with highest fuzzy score
        best, score, _ = process.extractOne(surname, hits or _reference_names,
                                            scorer=fuzz.token_set_ratio)
        if score >= 90:                 # very strict: need perfect surname match
            return best


    match, score, _ = process.extractOne(query, _reference_names, scorer=fuzz.token_set_ratio) or (None, 0, None)
    return match if score >= 75 else None
