import json

from elli_billing_tool.config import Config
from elli_billing_tool.cli import main


def _settings():
    return {
        "_comment": "preserve me",
        "ELLI_EMAIL": "must-not-print@example.invalid",
        "ELLI_PASSWORD": "must-not-print-secret",
        "ELLI_STATION_ID": "station",
        "ELLI_RFID_CARD_ID": "",
        "ELLI_KWH_PRICE_CENTS": "30",
        "ELLI_LOCATION": "Berlin",
        "ELLI_CURRENT_MONTH": False,
        "EMAIL_SUBJECT": "Subject",
        "EMAIL_RECIPIENTS": "accounting@example.invalid",
        "EMAIL_CC": "",
        "EMAIL_NAME": "Name",
    }


def test_old_credentials_are_ignored_removed_and_never_printed(tmp_path, capsys):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(_settings()), encoding="utf-8")
    config = Config.load_from_file(path)
    migrated = json.loads(path.read_text(encoding="utf-8"))
    assert config.station_id == "station"
    assert "ELLI_EMAIL" not in migrated and "ELLI_PASSWORD" not in migrated
    assert migrated["_comment"] == "preserve me"
    output = capsys.readouterr().out
    assert "must-not-print" not in output


def test_status_contains_no_token_value(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["elli-billing-tool", "status"])
    monkeypatch.setattr("elli_billing_tool.cli.TokenStore.has_credentials", lambda self: True)
    main()
    assert capsys.readouterr().out.strip() == "Elli-Konto lokal verbunden: ja"
