# Vektordatenbank-Demo

Lokale deutschsprachige Streamlit-Demo für semantische Suche mit Qdrant und Sentence-Transformers.

## Voraussetzungen

- Windows mit PowerShell
- Docker Desktop mit laufendem Docker-Dienst
- Python 3.11 oder neuer, im lokalen Setup geprüft mit Python 3.14

## Schnellstart

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
.\start.ps1
```

Manuell:

```powershell
docker compose up -d
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Die App ist anschließend unter `http://localhost:8501` erreichbar. Der Qdrant-Healthcheck liegt unter `http://127.0.0.1:6333/healthz`.
Änderungen an Python-Dateien werden automatisch in die laufende App übernommen. Der Datei-Watcher ignoriert `.venv` und `qdrant_storage`; unten rechts zeigt ein Timer die Zeit seit dem letzten Hot Reload. Nach jeder Suche wird die Uhrzeit der letzten Suchanfrage einschließlich Millisekunden angezeigt.
Streamlit untersucht außerdem optionale Bildverarbeitungsmodule von Transformers. Die dadurch entstehenden Watcher-Meldungen zu fehlendem `torchvision` werden einmalig zusammengefasst; die Textsuche benötigt diese Abhängigkeit nicht.
Das Hugging-Face-Modell wird beim ersten Start aus dem Internet heruntergeladen, falls es noch nicht im lokalen Cache liegt. Danach wird die lokale Kopie wiederverwendet. Für den ersten Download ist eine Internetverbindung erforderlich.

## Konfiguration

Kopiere `.env.example` bei Bedarf nach `.env`. Die Anwendung liest Umgebungsvariablen; die aktuelle Demo lädt `.env` nicht automatisch, daher müssen Variablen in PowerShell gesetzt oder über die Startumgebung bereitgestellt werden.

| Variable | Standard | Bedeutung |
|---|---:|---|
| `QDRANT_HOST` | `localhost` | Qdrant-Host |
| `QDRANT_PORT` | `6333` | REST-Port |
| `QDRANT_TIMEOUT` | `5` | Client-Timeout in Sekunden |
| `QDRANT_API_KEY` | leer | Optionaler API-Key |
| `QDRANT_COLLECTION` | `space_objects` | Collection-Name |
| `EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | Sentence-Transformer-Modell |
| `EMBEDDING_DIMENSION` | `384` | Erwartete Vektordimension |
| `MAX_NAME_LENGTH` | `120` | Maximale Namenslänge |
| `MAX_DESCRIPTION_LENGTH` | `2000` | Maximale Beschreibungslänge |
| `MAX_SEARCH_LIMIT` | `50` | Obergrenze für Suchtreffer |

## Architektur

- `streamlit_app.py`: Einstiegspunkt, Navigation, aktiver Nutzer und Datenverwaltung.
- `database.py`: Qdrant, Embeddings, CRUD, serverseitige Nutzerfilter und Batch-Operationen.
- `config.py`, `validation.py`, `errors.py`: zentrale Konfiguration, Eingabeprüfung und Fehlerklassen.
- `app_pages/`: Demo- und Erklärseiten.
- `app_state.py`, `data_access.py`: Session-State und versionsgebundene Lesecaches.
- `tests/`: Unit-Tests für Validierung und Nutzerisolierung.

Die Collection `space_objects` bleibt bei 384 Dimensionen und Cosine-Distanz kompatibel. Beim Start wird der Keyword-Index auf `user_id` idempotent angelegt. Eine inkompatible bestehende Collection wird nicht stillschweigend gelöscht.

## Nutzertrennung

Die Demo simuliert `Nutzer A` und `Nutzer B`. Jede nutzerbezogene Liste, Suche, Zählung, Aktualisierung und Löschung wird mit einem serverseitigen Qdrant-Filter auf `user_id` ausgeführt. Einzelaktionen kombinieren zusätzlich die UUID mit diesem Filter. Fremde UUIDs werden abgewiesen.

Das ist keine echte Authentifizierung. Der Nutzer wird nur aus einer festen Whitelist ausgewählt.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q .
```

Integrationstests gegen Qdrant sollten eine eigene Test-Collection verwenden; die Produktiv-Collection `space_objects` darf dafür nicht gelöscht werden.

## Demo versus Produktion

Für einen echten Betrieb fehlen insbesondere:

- echte Authentifizierung und Autorisierung statt simuliertem Nutzerwechsel,
- Qdrant-API-Key, TLS und Netzwerksegmentierung,
- getrennte Mandantenstrategie bzw. geprüfte Qdrant-Multitenancy,
- Backups, Wiederherstellungstests, Audit-Logging und Rate-Limiting,
- Secret-Management außerhalb des Repositories,
- Monitoring und zentrale Fehler- bzw. Sicherheitsauswertung.

`qdrant_storage/` enthält lokale persistente Demo-Daten und gehört nicht in ein produktives Repository. Es wird durch `.gitignore` ausgeschlossen.

## Fehlerbehebung

- Qdrant nicht erreichbar: `docker compose ps` und `docker compose logs qdrant` prüfen, danach `docker compose up -d` ausführen.
- Modell-Download schlägt fehl: Internetverbindung und Schreibrechte des lokalen Hugging-Face-Caches prüfen.
- Collection inkompatibel: keine Daten löschen; Konfiguration und bestehende Migration bewusst prüfen.
