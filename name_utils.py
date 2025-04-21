# name_utils.py
import csv
from functools import lru_cache
from rapidfuzz import process, fuzz
import numpy as np


def canonize_score_tokens(tokens):
    """
    Normalize raw token list into [team1, s1, r1, team2, s2, r2], or None.
    """
    if len(tokens) == 6:
        return tokens
    if len(tokens) == 8:
        team1 = tokens[0] + "/" + tokens[1]
        s1, r1 = tokens[2], tokens[3]
        team2 = tokens[4] + "/" + tokens[5]
        s2, r2 = tokens[6], tokens[7]
        return [team1, s1, r1, team2, s2, r2]
    return None


def extract_name_spans(canon_tokens):
    """
    Given canonical [team1, s1, r1, team2, s2, r2], return [team1, team2].
    """
    return [canon_tokens[0], canon_tokens[3]]


def raw_token_lists_from_data(all_data):
    """
    Flatten OCR results into list of (frame_idx, [tokens]).
    """
    token_lists = []
    replacements = {"O": "0"}
    for ok, idx, result in all_data:
        if not ok or result is None or (isinstance(result, str) and "OPTIM" in result):
            continue
        det = result[0]
        if det is None:
            continue
        tokens = [r[1][0] for r in det]
        for i, t in enumerate(tokens):
            if t in replacements:
                tokens[i] = replacements[t]
            if "." in tokens[i]:
                tokens[i] = tokens[i].replace(".", "")
        token_lists.append((idx, tokens))
    return token_lists


def load_reference_names(csv_path="./data/player_list.csv"):
    """
    Load master list of player names (uppercased, whitespace normalized).
    """
    refs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            name = row[0].strip().upper()
            if name:
                refs.append(" ".join(name.split()))
    return refs


@lru_cache(maxsize=None)
def cached_match_name(span, reference_names):
    """
    Memoized matcher for single or doubles spans; supports exact, reversed, and fuzzy.
    """
    query = span.replace("-", " ").upper().strip()
    query = " ".join(query.split())

    # Doubles: split on '/'
    if "/" in query:
        parts = [p.strip() for p in query.split("/")]
        matched = []
        for part in parts:
            # Attempt exact full-name
            if part in reference_names:
                matched.append(part)
                continue
            # Attempt reversed full-name 'Last First'
            tokens = part.split()
            if len(tokens) > 1:
                rev = " ".join(tokens[::-1])
                if rev in reference_names:
                    matched.append(rev)
                    continue
            # Exact surname if single token
            if len(tokens) == 1:
                surname = tokens[0]
                hits = [name for name in reference_names if name.split()[-1] == surname]
                if len(hits) == 1:
                    matched.append(hits[0])
                    continue
            # Fuzzy match fallback
            scores = process.cdist([part], reference_names, scorer=fuzz.token_set_ratio)
            idx = int(np.argmax(scores[0]))
            top_score = scores[0][idx]
            if top_score >= 80:
                matched.append(reference_names[idx])
            else:
                return None
        return " / ".join(matched)

    # Single: exact full-name
    if query in reference_names:
        return query
    # Single: reversed full-name
    tokens = query.split()
    if len(tokens) > 1:
        rev = " ".join(tokens[::-1])
        if rev in reference_names:
            return rev
    # Single: exact surname
    if len(tokens) == 1:
        surname = tokens[0]
        hits = [name for name in reference_names if name.split()[-1] == surname]
        if len(hits) == 1:
            return hits[0]
    # Single: fuzzy full-name
    scores = process.cdist([query], reference_names, scorer=fuzz.token_set_ratio)
    idx = int(np.argmax(scores[0]))
    top_score = scores[0][idx]
    if top_score >= 75:
        return reference_names[idx]
    return None
