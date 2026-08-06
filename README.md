# Elli Billing Tool

Das Tool lädt monatliche Ladevorgänge von Elli als PDF, liest den Verbrauch aus und erzeugt daraus das vorhandene Abrechnungsformular. Die Elli-Anmeldung findet interaktiv im normalen Systembrowser statt; das Tool verarbeitet oder speichert kein Elli-Passwort.

## Installation für die Entwicklung

Voraussetzung ist Python 3.11 oder neuer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
cp settings.json.example settings.json
```

`elli-client>=1.5.0` wird aus PyPI verwendet. Für Client-Entwicklung kann stattdessen vorübergehend `python -m pip install -e ../elli-client` benutzt werden.

Das eigene PDF-Template muss als `template/Template_Abrechnungsformular-Energiekosten-Firmenwagen-zuhause.pdf` vorliegen.

## Anmeldung und Verwendung

Beim ersten normalen Start öffnet sich die Elli-Seite im Standardbrowser. Dort anmelden, gegebenenfalls Cloudflare Turnstile bestätigen und erlauben, dass der Browser „Elli Login Callback“ öffnet. Danach wird die Abrechnung fortgesetzt.

```bash
elli-billing-tool                 # Standard: authentifizieren und Abrechnung erzeugen
elli-billing-tool generate
elli-billing-tool login
elli-billing-tool status
elli-billing-tool logout
elli-billing-tool list
```

`status` zeigt ausschließlich `Elli-Konto lokal verbunden: ja/nein`. `logout` löscht nur den lokalen Refresh-Token; es behauptet keine serverseitige Abmeldung. Bei weiteren Starts wird der Refresh-Token erneuert und eine mögliche Rotation sofort gespeichert. Nur wenn Elli eine erneute Anmeldung verlangt, wird der alte Token gelöscht und der Browser erneut geöffnet. Temporäre Netzwerkfehler löschen ihn nicht.

## Konfiguration

`settings.json` enthält weiterhin Station, optionale RFID-Karte, Strompreis, Ort, Zeitraum und Maildaten. `ELLI_EMAIL` und `ELLI_PASSWORD` sind veraltet, werden ignoriert und bei sicher möglicher Migration entfernt. Das Tool fragt kein Elli-Passwort ab.

## Lokale Tokens und Datenschutz

Der Refresh-Token liegt unter macOS im Schlüsselbund und unter Windows im Credential Manager (über `keyring`). Tokens stehen weder in `settings.json` noch im Programmordner und werden nicht ausgegeben. Wenn der Betriebssystem-Schlüsselspeicher nicht verfügbar ist, bricht das Tool verständlich ab.

Ein expliziter Fallback kann für kontrollierte Sonderumgebungen mit `ELLI_BILLING_TOKEN_FALLBACK=file` aktiviert werden. Er schreibt atomisch in das plattformspezifische App-Datenverzeichnis (`~/Library/Application Support/Elli Billing Tool/` bzw. `%LOCALAPPDATA%\Elli Billing Tool\`) und nutzt unter Unix Modus `0600`. Dieser Fallback ist schwächer als Keychain/Credential Manager.

Die Anmeldung läuft ausschließlich auf der Elli-Webseite. Es gibt keinen eingebetteten Browser, CAPTCHA-Bypass, Passwort-POST oder Cloud-Relay; der Callback wird lokal über `127.0.0.1` an den wartenden Prozess weitergereicht.

## macOS

Die Distribution enthält `elli-billing-tool.exec`, `run.sh` und die fensterlose `Elli Login Callback.app`. `run.sh` setzt das Arbeitsverzeichnis, meldet konkurrierende lokale Registrierungen für das Elli-Callback-Scheme sichtbar ab und registriert danach den mitgelieferten Helper idempotent bei Launch Services. Dabei werden keine App-Dateien gelöscht. Der Build versiegelt den Helper mit einer reproduzierbaren Ad-hoc-Signatur, damit das App-Bundle intern konsistent ist. Test-Builds können trotzdem eine Gatekeeper-Warnung auslösen; dann unter **Datenschutz & Sicherheit → Dennoch öffnen** freigeben. Die Ad-hoc-Signatur ersetzt keine Developer-ID-Signierung oder Notarisierung.

## Windows

Beim ersten interaktiven Login registriert das Tool seine tatsächlich laufende EXE unter `HKEY_CURRENT_USER\Software\Classes\com.elli.ios.emsp`; Administratorrechte sind nicht nötig. Ein fremder vorhandener Handler wird nicht überschrieben. Die interne Form `elli-billing-tool.exe oauth-callback "<URL>"` ist nicht für manuelle Verwendung bestimmt. Unsigned Builds können SmartScreen auslösen.

## Entwicklung und Tests

```bash
python -m pytest
pyinstaller elli-billing-tool.spec
```

Die PDF-/Berechnungslogik befindet sich unverändert in `pdf_parser.py` und `pdf_generator.py`. Automatisierte Auth-Tests verwenden ausschließlich Mocks und lokale Loopback-Verbindungen.
