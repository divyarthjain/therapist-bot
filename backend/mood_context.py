from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


class MoodContextStore:
    """Persists periodic mood snapshots for quiet therapist context."""

    def __init__(self, root: Optional[Path] = None, interval_seconds: float = 5.0):
        self.root = root or Path(__file__).resolve().parent / "runtime" / "mood_logs"
        self.root.mkdir(parents=True, exist_ok=True)
        self.interval_seconds = interval_seconds
        self._last_write_by_session: dict[str, float] = {}

    def _path_for(self, session_id: str) -> Path:
        safe_session = "".join(
            character for character in session_id if character.isalnum() or character in {"-", "_"}
        )
        return self.root / f"{safe_session or 'default'}.jsonl"

    def record_snapshot(self, session_id: str, fused_emotion: dict) -> bool:
        now = time.time()
        last_write = self._last_write_by_session.get(session_id, 0.0)
        if now - last_write < self.interval_seconds:
            return False

        snapshot = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "dominant": fused_emotion.get("dominant", "neutral"),
            "confidence": round(fused_emotion.get("confidence", 0.0), 4),
            "audio": {
                "emotion": fused_emotion.get("audio", {}).get("emotion", "neutral"),
                "confidence": round(
                    fused_emotion.get("audio", {}).get("confidence", 0.0), 4
                ),
            },
            "video": {
                "emotion": fused_emotion.get("video", {}).get("emotion", "neutral"),
                "confidence": round(
                    fused_emotion.get("video", {}).get("confidence", 0.0), 4
                ),
            },
        }

        with self._path_for(session_id).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(snapshot) + "\n")

        self._last_write_by_session[session_id] = now
        return True

    def summarize_recent(self, session_id: str, max_entries: int = 6) -> str:
        path = self._path_for(session_id)
        if not path.exists():
            return ""

        entries = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        if not entries:
            return ""

        recent_entries = entries[-max_entries:]
        lines = []
        for entry in recent_entries:
            lines.append(
                f"- {entry['timestamp']}: dominant={entry['dominant']} ({entry['confidence']:.0%}), "
                f"voice={entry['audio']['emotion']} ({entry['audio']['confidence']:.0%}), "
                f"face={entry['video']['emotion']} ({entry['video']['confidence']:.0%})"
            )
        return "\n".join(lines)
