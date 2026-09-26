import json
import shutil
from pathlib import Path

from receptionist.simulate import SCRIPT, resolve_config_path, run

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_resolve_config_path_falls_back_to_example(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    shutil.copy(REPO_ROOT / "business.example.yaml", tmp_path / "business.example.yaml")
    path = resolve_config_path(None)
    assert path == "business.example.yaml"


def test_scripted_run_exercises_tools_and_exits(tmp_path, monkeypatch, capsys):
    shutil.copy("business.example.yaml", tmp_path / "business.yaml")
    monkeypatch.chdir(tmp_path)

    run("business.yaml", interactive=False)

    captured = capsys.readouterr()
    assert "Sunrise Dental" in captured.out
    assert "Goodbye" in captured.out

    bookings = (tmp_path / "data" / "bookings.jsonl").read_text().strip().splitlines()
    assert len(bookings) == 1
    record = json.loads(bookings[0])
    assert record["service"] == "teeth cleaning"


def test_scripted_run_with_custom_lines(tmp_path, monkeypatch, capsys):
    shutil.copy("business.example.yaml", tmp_path / "business.yaml")
    monkeypatch.chdir(tmp_path)

    run("business.yaml", interactive=False, lines=["What are your hours?", "goodbye"])

    captured = capsys.readouterr()
    assert captured.err == ""
    assert "Goodbye" in captured.out


def test_default_script_is_nonempty():
    assert len(SCRIPT) > 0
