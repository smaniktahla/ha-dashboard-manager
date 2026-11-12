"""Store each kiosk playlist in its own JSON file."""
import argparse
import base64
import json
from pathlib import Path
import re
import tempfile

PLAYLIST_ID = re.compile(r"input_select[.]dashboard_manager_playlist_([a-z0-9_]+)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["read", "write"])
    parser.add_argument("playlist")
    parser.add_argument("payload", nargs="?")
    args = parser.parse_args()

    match = PLAYLIST_ID.fullmatch(args.playlist)
    if not match:
        parser.error("expected a Dashboard Manager kiosk playlist entity ID")
    path = Path(__file__).resolve().parent / "kiosk_playlists" / f"{match[1]}.json"

    if args.action == "read":
        print(path.read_text(encoding="utf-8") if path.exists() else "[]")
        return

    if not args.payload:
        parser.error("write requires a playlist payload")
    entries = json.loads(base64.b64decode(args.payload, validate=True))
    if not isinstance(entries, list) or not entries or not all(
        isinstance(entry, str) and entry for entry in entries
    ):
        parser.error("playlist must contain a nonempty list of dashboard entries")

    path.parent.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as staged:
        json.dump(entries, staged, ensure_ascii=False, indent=2)
        staged.write("\n")
    temporary_path = Path(staged.name)
    try:
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
