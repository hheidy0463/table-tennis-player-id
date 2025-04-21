#!/usr/bin/env python
import os, sys, csv, pickle, time
from tqdm import tqdm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.name_utils import (
    cached_match_name,
    raw_token_lists_from_data,
    canonize_score_tokens,
)

# ── config ────────────────────────────────────────────────────────────────
data_root = "./data/samples"
MAX_FRAMES_PER_CLIP = 40        # examine at most 40 frames per clip

results = []
clip_list = sorted(os.listdir(data_root))
print("Total clips:", len(clip_list))

# ── iterate clips ─────────────────────────────────────────────────────────
for clip_dir in tqdm(clip_list, desc="clips"):
    sb_path = os.path.join(data_root, clip_dir, "sb", "sb.pkl")
    if not os.path.exists(sb_path):
        continue

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
        (idx, canon)
        for idx, tok in raws[:MAX_FRAMES_PER_CLIP]
        if (canon := canonize_score_tokens(tok))
    ]

    # de‑duplicate by the four name tokens
    uniq = {}
    for idx, c in canonicals:
        uniq.setdefault(tuple(c[:4]), (idx, c))
    canonicals = list(uniq.values())          # [(idx, canon), …]

    best_hits, best_score = None, -1

    for _, canon in canonicals:
        team1, _, _, team2, _, _ = canon
        parts = []
        for team in (team1, team2):
            parts += [p.strip() for p in team.split("/")] if "/" in team else [team.strip()]

        hits, part_scores, total = [], [], 0

        parts = [p for p in parts if p and not p.isdigit() and len(p) > 1]

        for p in parts:
            if not p or p.isdigit() or len(p) == 1:
                continue
            hit = cached_match_name(p)
            score = 100 if hit else 0
            # inside the scoring loop, right before `if score < 60` …
            if score < 60:
                # allow 55 for last‑ditch match
                if score >= 55:
                    hits.append(match)
                    part_scores.append(score)
                    total += score
                    continue
                total = -1
                break

            hits.append(hit)
            part_scores.append(score)
            total += score

        if total > best_score:
            best_score = total
            best_hits  = hits

        # early exit if every part ≥60 and we matched 2 or 4 names
        if part_scores and min(part_scores) >= 60 and len(hits) in (2, 4):
            best_hits = hits
            break

    # ── record players ─
    players = ["", "", "", ""]
    if best_hits:
        for i, name in enumerate(best_hits[:4]):
            players[i] = name or ""
    elif canonicals:                       # had frames but none ≥60 %
        team1 = canonicals[0][1][0]
        if team1.isdigit():
            pass         # leave players blank instead of recording “0”
        elif "/" in team1:
            players[:2] = [p.strip() for p in team1.split("/")[:2]]
        else:
            players[0] = team1

    else:
        tqdm.write(f"{clip_dir}: no canonical frames found")

    results.append((clip_dir, players))

# ── write outputs ─────────────────────────────────────────────────────────
with open("video_player_names_matched.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["clip_id", "player1", "player2", "player3", "player4"])
    for cid, pls in results:
        w.writerow([cid] + pls)

print("DONE → video_player_names_matched.csv")
