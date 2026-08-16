import json

import pytest

from src.i18n.loader import (
    FALLBACK_LOCALE,
    SUPPORTED_LOCALES,
    load_all_locales,
    load_locale,
    translate,
    validate_locales,
)


def test_every_locale_json_is_valid_and_loads():
    for locale in SUPPORTED_LOCALES:
        strings = load_locale(locale)
        assert isinstance(strings, dict)
        assert len(strings) > 0


def test_every_en_key_present_in_hi_and_kn():
    en_keys = set(load_locale("en"))
    hi_keys = set(load_locale("hi"))
    kn_keys = set(load_locale("kn"))

    assert en_keys - hi_keys == set()
    assert en_keys - kn_keys == set()


def test_validate_locales_returns_empty_for_complete_locales():
    assert validate_locales() == {}


def test_validate_locales_writes_report_file(tmp_path):
    report_path = tmp_path / "report.json"
    validate_locales(report_path=report_path)
    assert report_path.exists()
    assert json.loads(report_path.read_text()) == {}


def test_validate_locales_detects_a_missing_key(tmp_path, monkeypatch):
    from src.i18n import loader

    locales_dir = tmp_path / "locales"
    locales_dir.mkdir()
    (locales_dir / "en.json").write_text(json.dumps({"a": "A", "b": "B"}))
    (locales_dir / "hi.json").write_text(json.dumps({"a": "अ"}))  # missing "b"
    (locales_dir / "kn.json").write_text(json.dumps({"a": "ಅ", "b": "ಬ"}))

    monkeypatch.setattr(loader, "LOCALES_DIR", locales_dir)
    report_path = tmp_path / "report.json"
    missing = loader.validate_locales(report_path=report_path)

    assert missing == {"hi": ["b"]}
    assert json.loads(report_path.read_text()) == {"hi": ["b"]}


def test_load_all_locales_raises_on_incomplete_locale(tmp_path, monkeypatch):
    from src.i18n import loader

    locales_dir = tmp_path / "locales"
    locales_dir.mkdir()
    (locales_dir / "en.json").write_text(json.dumps({"a": "A", "b": "B"}))
    (locales_dir / "hi.json").write_text(json.dumps({"a": "अ"}))
    (locales_dir / "kn.json").write_text(json.dumps({"a": "ಅ", "b": "ಬ"}))

    monkeypatch.setattr(loader, "LOCALES_DIR", locales_dir)
    monkeypatch.setattr(loader, "MISSING_KEYS_REPORT_PATH", tmp_path / "report.json")

    with pytest.raises(ValueError):
        loader.load_all_locales()


def test_load_all_locales_succeeds_for_the_real_locale_files():
    locales = load_all_locales()
    assert set(locales) == set(SUPPORTED_LOCALES)


def test_translate_returns_locale_specific_string():
    assert translate("common.save", "kn") != translate("common.save", "en")


def test_translate_falls_back_to_english_for_a_missing_key(tmp_path, monkeypatch):
    from src.i18n import loader

    locales_dir = tmp_path / "locales"
    locales_dir.mkdir()
    (locales_dir / "en.json").write_text(json.dumps({"only_in_en": "hello"}))
    (locales_dir / "hi.json").write_text(json.dumps({}))
    (locales_dir / "kn.json").write_text(json.dumps({}))

    monkeypatch.setattr(loader, "LOCALES_DIR", locales_dir)
    assert loader.translate("only_in_en", "hi") == "hello"


def test_load_locale_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_locale("not_a_real_locale")


def test_fallback_locale_is_english():
    assert FALLBACK_LOCALE == "en"
