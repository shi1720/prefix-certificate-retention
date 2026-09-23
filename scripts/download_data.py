"""Fetch pinned, hash-checked Mooncake traces. Does not query a model API."""
from pathlib import Path
import json, hashlib, urllib.request

root = Path(__file__).resolve().parents[1]
for entry in json.loads((root/'data/manifest.json').read_text()):
    destination = root/'data/raw'/f"{entry['name']}.jsonl"
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = destination.read_bytes() if destination.exists() else urllib.request.urlopen(entry['url'], timeout=60).read()
    if hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise RuntimeError(f"Hash mismatch for {entry['name']}")
    destination.write_bytes(data)
    print(entry['name'], 'verified', len(data), 'bytes')
