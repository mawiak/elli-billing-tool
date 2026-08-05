# Elli Billing Tool – Kurzanleitung

1. ZIP entpacken und `settings.json` mit Station, Strompreis, Ort und Maildaten ausfüllen. E-Mail und Elli-Passwort werden nicht benötigt.
2. Das eigene Formular nach `template/Template_Abrechnungsformular-Energiekosten-Firmenwagen-zuhause.pdf` kopieren.
3. macOS: `./run.sh`; Windows: `run.bat` starten.
4. Beim ersten Start im normalen Browser bei Elli anmelden, Cloudflare bestätigen und das Öffnen von „Elli Login Callback“ erlauben.
5. Das Tool lädt das Elli-PDF, erzeugt das Abrechnungs-PDF und öffnet anschließend wie bisher Mailprogramm und Ausgabeordner.

Weitere Starts benötigen keinen Browser, solange der Refresh-Token gültig ist.

## Diagnose

macOS:

```bash
./run.sh logout
./run.sh status
./run.sh login
./run.sh status
./run.sh
```

Windows entsprechend mit `run.bat logout`, `run.bat status`, `run.bat login`, `run.bat status` und `run.bat`.

Bei einem unsignierten macOS-Testbuild kann **Datenschutz & Sicherheit → Dennoch öffnen** erforderlich sein. Bei Windows kann SmartScreen warnen. Produktive Releases sollten mit Apple Developer ID signiert/notarisiert beziehungsweise mit einem Windows-Code-Signing-Zertifikat signiert werden.

`logout` löscht nur lokale Tokens. Loginprobleme geben keine Callback-URL, Codes oder Tokens aus.
