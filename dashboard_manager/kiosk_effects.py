"""Per-kiosk screen and dashboard-transition effect settings, stored as one JSON file.

The file lives in /config/www so each kiosk can fetch it (unauthenticated, non-sensitive) from
http://<ha>/local/kiosk_effects.json and follow edits made in the Dashboard Manager UI live.
Keeping it on disk, not only in helper states, means it survives restarts and a lost restore_state.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import tempfile

FILE = Path(os.environ.get("KIOSK_EFFECTS_FILE", "/config/www/kiosk_effects.json"))
MODES = ("none", "fade", "crossfade")
DEFAULTS = {
    "transition_mode": "fade",    # none | fade | crossfade (dashboard to dashboard)
    "transition_seconds": 0.6,    # length of each fade / the crossfade blend
    "transition_hold": 0.5,       # seconds for the new dashboard to render before fading back in
    "blank_fade": 1.5,            # screen blank: fade to black, seconds
    "wake_delay": 1.4,            # screen wake: seconds black while the monitor lights up
    "wake_fade": 1.0,             # screen wake: fade-in, seconds
}
LIMITS = {"transition_seconds": 5, "transition_hold": 5, "blank_fade": 5, "wake_delay": 6, "wake_fade": 5}
KIOSK = __import__("re").compile(r"[A-Za-z0-9_-]{1,64}")


def clean(values):
    out = dict(DEFAULTS)
    for key, value in (values or {}).items():
        if key == "transition_mode":
            if value in MODES:
                out[key] = value
        elif key in LIMITS:
            try:
                out[key] = round(min(max(float(value), 0.0), LIMITS[key]), 2)
            except (TypeError, ValueError):
                pass
    return out


def load():
    try:
        data = json.loads(FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["read", "write"])
    parser.add_argument("kiosk")
    parser.add_argument("payload", nargs="?", help="base64 JSON object (write)")
    args = parser.parse_args()
    if not KIOSK.fullmatch(args.kiosk):
        parser.error("kiosk must be a Browser Mod browser id")
    data = load()
    if args.action == "read":
        print(json.dumps(clean(data.get(args.kiosk))))
        return
    if not args.payload:
        parser.error("write requires a payload")
    values = json.loads(base64.b64decode(args.payload, validate=True))
    if not isinstance(values, dict):
        parser.error("payload must be a JSON object")
    data[args.kiosk] = clean(values)
    FILE.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=FILE.parent, delete=False) as staged:
        json.dump(data, staged, indent=2, sort_keys=True)
    os.chmod(staged.name, 0o644)
    os.replace(staged.name, FILE)
    print(json.dumps(data[args.kiosk]))


if __name__ == "__main__":
    main()
