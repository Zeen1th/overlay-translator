import json
from overlay_translator.history_store import HistoryStore, HistoryEntry, MAX_ENTRIES


def test_add_is_newest_first_and_persists(tmp_path):
    p = str(tmp_path / "history.json")
    store = HistoryStore(p)
    store.add("Hello", "مرحبا", "2026-07-11T10:00:00")
    store.add("Bye", "وداعا", "2026-07-11T10:01:00")
    entries = store.entries()
    assert entries[0].source == "Bye"        # newest first
    assert entries[1].source == "Hello"
    # persisted: a fresh store on the same path sees the same data
    assert HistoryStore(p).entries()[0].translation == "وداعا"


def test_cap_at_max_entries(tmp_path):
    store = HistoryStore(str(tmp_path / "h.json"))
    for i in range(MAX_ENTRIES + 25):
        store.add(f"s{i}", f"t{i}", "2026-07-11T10:00:00")
    assert len(store.entries()) == MAX_ENTRIES
    assert store.entries()[0].source == f"s{MAX_ENTRIES + 24}"  # newest kept


def test_delete_by_index(tmp_path):
    store = HistoryStore(str(tmp_path / "h.json"))
    store.add("a", "A", "t")
    store.add("b", "B", "t")   # entries: [b, a]
    store.delete(0)            # remove b
    assert [e.source for e in store.entries()] == ["a"]


def test_clear(tmp_path):
    store = HistoryStore(str(tmp_path / "h.json"))
    store.add("a", "A", "t")
    store.clear()
    assert store.entries() == []


def test_corrupt_file_starts_empty(tmp_path):
    p = tmp_path / "h.json"
    p.write_text("not json", encoding="utf-8")
    assert HistoryStore(str(p)).entries() == []


def test_ids_are_unique_and_nonzero(tmp_path):
    store = HistoryStore(str(tmp_path / "h.json"))
    for i in range(5):
        store.add(f"s{i}", f"t{i}", "2026-07-11T10:00:00")
    ids = [e.id for e in store.entries()]
    assert all(i != 0 for i in ids)
    assert len(set(ids)) == len(ids)


def test_delete_by_id_removes_targeted_entry(tmp_path):
    store = HistoryStore(str(tmp_path / "h.json"))
    store.add("a", "A", "t")
    store.add("b", "B", "t")   # entries: [b, a]
    target = store.entries()[1]  # "a"
    assert store.get_by_id(target.id) == target
    store.delete_by_id(target.id)
    assert [e.source for e in store.entries()] == ["b"]
    assert store.get_by_id(target.id) is None
