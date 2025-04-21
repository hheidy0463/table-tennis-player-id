#!/usr/bin/env python
import os, sys, csv, pickle, time
from tqdm import tqdm
from rapidfuzz import process, fuzz

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import util
from name_utils import (
    load_reference_names,
    raw_token_lists_from_data,
    canonize_score_tokens,
)

# ── config ────────────────────────────────────────────────────────────────
data_root = "./data/samples"
MAX_FRAMES_PER_CLIP = 40        # stop after this many canonical frames

# ── load & normalise refs once ────────────────────────────────────────────
ref_raw = load_reference_names()
REFS = tuple(" ".join(r.replace("-", " ").split()) for r in ref_raw)

# tiny cache so we never fuzzy‑match same span twice
SPAN_CACHE = {}   # span -> (match, score)

def match_span(span: str):
    if span in SPAN_CACHE:
        return SPAN_CACHE[span]
    match, score, _ = process.extractOne(
        span, REFS, scorer=fuzz.token_set_ratio
    ) or (None, 0, None)
    SPAN_CACHE[span] = (match, score)
    return match, score

# ── iterate clips ─────────────────────────────────────────────────────────
results           = []
all_unknown_spans = []

clip_list = sorted(os.listdir(data_root))
print("Total clips:", len(clip_list))

for clip_dir in tqdm(clip_list, desc="clips"):
    sb_path = os.path.join(data_root, clip_dir, "sb", "sb.pkl")
    if not os.path.exists(sb_path):
        continue

    t0 = time.time()

    # ── load OCR pickles ─
    all_data = []
    with open(sb_path, "rb") as f:
        while True:
            try:
                all_data.extend(pickle.load(f))
            except EOFError:
                break

    # ── flatten & canonicalise ─
    raws = raw_token_lists_from_data(all_data)
    canonicals = [
        canonize_score_tokens(tok)
        for _, tok in raws[: MAX_FRAMES_PER_CLIP]  # <-- limit frames
        if canonize_score_tokens(tok)
    ]

    # remove duplicate frames
    canonicals = list(dict.fromkeys(tuple(c) for c in canonicals))

    best_hits  = None
    best_score = -1

    for canon in canonicals:
        team1, _, _, team2, _, _ = canon
        parts = []
        for team in (team1, team2):
            if "/" in team:
                parts += [p.strip() for p in team.split("/")]
            else:
                parts.append(team.strip())

        total = 0
        hits  = []
        for p in parts:
            hit, score = match_span(p)
            if score < 60:
                total = -1
                break
            hits.append(hit)
            total += score

        if total > best_score:
            best_score = total
            best_hits  = hits

    # ── record players ─
    # ── record players ─
    players = ["", "", "", ""]

    if best_hits:                           # normal case
        for i, name in enumerate(best_hits[:4]):
            players[i] = name or ""

    elif canonicals:                        # we had frames but none passed 60 %
        team1 = canonicals[0][0]            # first team string for sanity‑check
        if "/" in team1:
            players[:2] = [p.strip() for p in team1.split("/")[:2]]
        else:
            players[0] = team1

    else:                                   # no valid canonical frames at all
        tqdm.write(f"{clip_dir}: no canonical frames found")

    results.append((clip_dir, players))


# ── write outputs ─────────────────────────────────────────────────────────
with open("video_player_names_matched.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["clip_id", "player1", "player2", "player3", "player4"])
    for cid, pls in results:
        w.writerow([cid] + pls)

print("DONE → video_player_names_matched.csv")
