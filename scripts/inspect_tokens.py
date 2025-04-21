#!/usr/bin/env python
import os, pickle, re
from collections import Counter
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.name_utils import raw_token_lists_from_data

DATA_ROOT = "./data/samples"
lengths  = Counter()
examples = {}

for clip in sorted(os.listdir(DATA_ROOT)):
    sb = os.path.join(DATA_ROOT, clip, "sb", "sb.pkl")
    if not os.path.exists(sb):
        continue

    with open(sb, "rb") as f:
        all_data = []
        while True:
            try:
                all_data.extend(pickle.load(f))
            except EOFError:
                break

    # tokenize all at once, skip bad frames
    raws = raw_token_lists_from_data(all_data)
    for idx, toks in raws:
        L = len(toks)
        lengths[L] += 1
        # keep up to 3 examples per length
        if len(examples.setdefault(L, [])) < 3:
            examples[L].append((clip, toks))

print("Token‐length distribution:\n")
for L, cnt in sorted(lengths.items()):
    print(f"  {L:2d} tokens: {cnt} detections")
    for clip, tok in examples[L]:
        print("    ", clip, tok)
    print()
