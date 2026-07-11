import json
import os
from dataclasses import asdict, dataclass

MAX_ENTRIES = 200


@dataclass
class HistoryEntry:
    source: str
    translation: str
    timestamp: str


class HistoryStore:
    """Newest-first translation history persisted to a JSON file."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._entries: list[HistoryEntry] = self._load()

    def _load(self) -> list[HistoryEntry]:
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return [
                HistoryEntry(
                    source=item["source"],
                    translation=item["translation"],
                    timestamp=item["timestamp"],
                )
                for item in data
            ]
        except (OSError, ValueError, KeyError, TypeError):
            print("[history] could not read history file; starting empty.")
            return []

    def _save(self) -> None:
        tmp = self._path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump([asdict(e) for e in self._entries], fh,
                      indent=2, ensure_ascii=False)
        os.replace(tmp, self._path)

    def entries(self) -> list[HistoryEntry]:
        return list(self._entries)

    def add(self, source: str, translation: str, timestamp: str) -> None:
        self._entries.insert(0, HistoryEntry(source, translation, timestamp))
        del self._entries[MAX_ENTRIES:]
        self._save()

    def delete(self, index: int) -> None:
        if 0 <= index < len(self._entries):
            del self._entries[index]
            self._save()

    def clear(self) -> None:
        self._entries = []
        self._save()
