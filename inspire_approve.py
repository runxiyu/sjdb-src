#!/usr/bin/env python3

from __future__ import annotations
import json
import sys

for fn in sys.argv[1:]:
    with open(fn, "r", encoding="utf-8") as fd:
        jq = json.load(fd)
        jq["approved"] = True
        json.dump(fd, jq, indent="\t")
