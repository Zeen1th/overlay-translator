import json
import os
from dataclasses import asdict, dataclass

MAX_ENTRIES = 200


@dataclass
class HistoryEntry:
    source: str
    translation: str
    timestamp: str
    id: int = 0


class HistoryStore:
    """Newest-first translation history persisted to a JSON file."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._entries: list[HistoryEntry] = self._load()
        self._next_id = 1 + max((e.id for e in self._entries), default=0)

    def _load(self) -> list[HistoryEntry]:
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            entries = [
                HistoryEntry(
                    source=item["source"],
                    translation=item["translation"],
                    timestamp=item["timestamp"],
                    id=item.get("id", 0),
                )
                for item in data
            ]
            used = {e.id for e in entries if e.id}
            nxt = (max(used) + 1) if used else 1
            for e in entries:
                if not e.id:
                    e.id = nxt
                    nxt += 1
            return entries
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
        entry = HistoryEntry(source, translation, timestamp, id=self._next_id)
        self._next_id += 1
        self._entries.insert(0, entry)
        del self._entries[MAX_ENTRIES:]
        self._save()

    def delete(self, index: int) -> None:
        if 0 <= index < len(self._entries):
            del self._entries[index]
            self._save()

    def delete_by_id(self, entry_id: int) -> None:
        self._entries = [e for e in self._entries if e.id != entry_id]
        self._save()

    def get_by_id(self, entry_id: int):
        for e in self._entries:
            if e.id == entry_id:
                return e
        return None

    def clear(self) -> None:
        self._entries = []
        self._save()
