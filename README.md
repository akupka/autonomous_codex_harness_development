[English version README.md here](README_english.md)
# Autonomer Agent Harness (Spec → Tests → Git → „until green“)

Dieses Repository enthält einen kleinen **Harness**, der einen autonomen Entwicklungs-Agenten steuert. Ziel ist es, ein Projekt anhand einer Spezifikation (`app_spec.txt`) und einer **testbaren Feature-/Testliste** (`feature_list.json`) iterativ so lange weiterzuentwickeln, bis **alle Tests grün** sind.

Idee von hier https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents in der ANTHROPIC_COMPPLIANCE.md verglichen mit dem Blog Post. (Ich habe kein Anthropic Account, aber die Idee ist super, deshlab auf Codex mit ein paar Erweiterungen umgesetzt.)

Die Automatisierung besteht aus drei Kernskripten:

- `run_init.sh` – Initialisiert ein neues Projekt (Prompt-gesteuert).
- `run_cycle.sh` – Führt **einen** Implementierungs-Zyklus aus 
- `run_until_green.sh` – Wiederholt Zyklen, bis alle Tests `passes: true` sind (oder Stop-Bedingungen greifen).

---

## Grundprinzip

1. **Spezifikation:** In `app_spec.txt` steht, *was* gebaut werden soll.
2. **Tests/Features als Harness:** In `feature_list.json` steht, *wie* geprüft wird, ob es fertig ist.
3. **Agent arbeitet Test-für-Test:** Der Coding-Agent sucht sich den nächsten Test mit `"passes": false`, implementiert die Funktion, verifiziert über die UI und setzt anschließend auf `"passes": true`.
4. **Git als Audit-Trail:** Jede Änderung wird committed. Optional kann nach jedem erfolgreichen Zyklus gepusht werden (siehe Konfiguration).

> Wichtig: Im Normalbetrieb soll in `feature_list.json` **nur** das Feld `passes` geändert werden (von `false` auf `true`). Beschreibungen/Schritte werden nicht „umgeschrieben“, damit das Harness stabil bleibt.

---

## Dateien und Verzeichnisstruktur

- `app_spec.txt`  
  Anforderungen / Spezifikation (Input).
- `feature_list.json`  
  Testkatalog (Single Source of Truth). Format: entweder JSON-Array `[...]` oder Objekt `{ "tests": [ ... ] }`.
- `codex-progress.txt`  
  Fortschrittsnotizen (was erledigt, was als nächstes).
- `init.sh`  
  Start-/Setup-Skript für die Projektumgebung (wird typischerweise beim Init erzeugt).
- `logs/`  
  Log-Dateien je Zyklus (`run_until_green.sh` schreibt hier hinein).
- `scripts/`  
  Dispatcher 

---

## Voraussetzungen

### Pflicht: Für den Harness (die Skripte)

Damit `run_init.sh`, `run_cycle.sh` und `run_until_green.sh` laufen, müssen folgende Tools installiert und im `PATH` verfügbar sein:

- **Bash** (Linux/macOS empfohlen; unter Windows am besten via **WSL**)
- **codex CLI** (`codex`)  
  Wird von `run_init.sh` und `run_cycle.sh` verwendet (`codex exec --yolo`).
- **Python 3** (`python3`)  
  Wird von `run_until_green.sh` und den Skripten genutzt.
- **Python-Pakete:** Keine externen Libraries nötig (nur Standardbibliothek).  
  Optional: `pip install -r requirements.txt` (bleibt bewusst leer).

Optional: Virtuelle Umgebung für Python
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
- **Git** (`git`)  
  Wird für den Audit-Trail (Commits) benötigt; außerdem für optionales Auto-Push.
- **OpenSSH-Tools** (`ssh-agent`, `ssh-add`)  
  Nur erforderlich wenn `push_each_cycle=1` in `harness.conf` gesetzt ist.
- **Standard Unix-Utilities** (typisch bereits vorhanden): `date`, `seq`, `mkdir`, `cat`, `chmod`, `timeout`


### Projekt-spezifisch: Abhängig von deiner `app_spec.txt`

Zusätzlich können je nach Tech-Stack erforderlich sein (und werden oft von `init.sh` genutzt/erwartet):

- **Node.js** + Paketmanager (`npm`/`pnpm`/`yarn`)
- **Python**-Tooling (`pip`, `poetry`, `venv`)
- **Docker / Docker Compose** (z.B. für DB/Redis)
- Datenbank-CLI/Clients (z.B. `psql`), falls im Projekt vorgesehen

Welche dieser Tools wirklich nötig sind, hängt von den Anforderungen und dem erzeugten `init.sh` ab.

---

## Neues Projekt anlegen – 6 Schritte

### Schritt 1: Projektordner erstellen und Harness-Dateien ablegen
Lege einen neuen Ordner an und kopiere hinein:
- `run_init.sh`
- `run_cycle.sh`
- `run_until_green.sh`
- deine Prompt-Dateien (z.B. `coding_prompt.md` und `init_prompt.md`)
- eine neue `app_spec.txt` (siehe Schritt 2)

### Schritt 2: `app_spec.txt` schreiben
Formuliere Anforderungen so, dass daraus konkrete End-to-End-Tests ableitbar sind:
- Kern-Features
- UI/UX-Anforderungen
- Validierungen/Fehlerfälle
- Rollen/Rechte (falls relevant)
- Integrationen/Datenpersistenz (falls relevant)

### Schritt 3: Initializer starten (erzeugt Baseline)
```bash
chmod +x run_init.sh
./run_init.sh
```

Falls deine Init-Prompt-Datei nicht `init_prompt.md` heißt:
```bash
INIT_PROMPT_FILE=DEIN_INIT_PROMPT.md ./run_init.sh
```

Erwartung nach Init (Baseline):
- `feature_list.json` ist vorhanden (umfangreicher Testkatalog)
- `init.sh` ist vorhanden (Environment-Setup)
- erste Git-Commits existieren (Projektstart dokumentiert)

### Schritt 4: Umgebung starten
```bash
chmod +x init.sh
./init.sh
```

### Schritt 5: ssh-agent sicherstellen (wird vom Loop geprüft)
`run_until_green.sh` erwartet einen aktiven `ssh-agent`:
```bash
eval $(ssh-agent -s)
ssh-add
```

### Schritt 6: Autonomen Loop starten („until green“)
```bash
chmod +x run_until_green.sh run_cycle.sh
./run_until_green.sh
```

Der Loop schreibt Logs nach `logs/` und läuft, bis alle Tests `passes: true` sind oder eine Stop-Bedingung greift.

---

## Projekt erweitern (Standardfall: Spec bleibt gleich)

Wenn du neue Commits willst, ohne die Spezifikation zu ändern:
1. Stelle sicher, dass die Umgebung läuft (`./init.sh`).
2. Starte den Loop:
   ```bash
   ./run_until_green.sh
   ```
3. Der Agent arbeitet die nächsten Tests mit `"passes": false` ab, verifiziert und markiert sie als passing.

---

## Projekt erweitern bei geänderter Spezifikation – 6 Schritte (Re-Baseline)

Wenn sich Anforderungen in `app_spec.txt` **ändern** (nicht nur additiv!), muss das Harness (`feature_list.json`) wieder zur Spezifikation passen. Sonst kämpfst du gegen veraltete/inkonsistente Tests.

### Schritt 1: Sauberen Checkpoint erstellen (vor der Änderung)
```bash
git add -A
git commit -m "Checkpoint before spec change"
git tag spec-v1-baseline
```

### Schritt 2: `app_spec.txt` aktualisieren und committen
```bash
git add app_spec.txt
git commit -m "Update app_spec to v2 requirements"
git tag spec-v2-requirements
```

### Schritt 3: Entscheiden: Additiv vs. Re-Baseline
- **Nur additiv (nur neue Features dazu):** Du kannst neue Tests ergänzen (auf `passes:false`).
- **Geändert/ersetzt/entfernt:** Re-Baseline ist empfohlen.

### Schritt 4: Alte Testliste archivieren
```bash
cp feature_list.json feature_list.v1.json
git add feature_list.v1.json
git commit -m "Archive feature_list v1"
```

### Schritt 5: Neue `feature_list.json` erzeugen (bewusst außerhalb Normalmodus)
Im Normalmodus soll `feature_list.json` nicht umgeschrieben werden (nur `passes`).
Für eine Re-Baseline nutze einen **separaten Prompt** (z.B. `spec_update_prompt.md`), der ausdrücklich erlaubt, die Liste passend zur neuen Spec neu zu generieren.

```bash
CYCLE_PROMPT_FILE=spec_update_prompt.md ./run_cycle.sh
```

Danach:
```bash
git add feature_list.json codex-progress.txt
git commit -m "Rebaseline feature_list to app_spec v2"
git tag spec-v2-tests
```

### Schritt 6: Wieder normal laufen lassen („until green“)
```bash
./run_until_green.sh
```

---

## Konfiguration (Environment-Variablen)

### Neue zentrale Config-Datei: harness.conf

Seit der aktuellen Version gibt es eine **zentrale Konfigurationsdatei** `harness.conf`, die alle wichtigen Parameter an einem Ort bündelt:

```bash
# Beispiel harness.conf
test_case_limit=50          # Für kleine Projekte: 20-50 Tests
cycle_prompt_file=coding_prompt.md
init_prompt_file=init_prompt.md
max_errors=10               # Mehr Fehler-Toleranz
push_each_cycle=0           # Kein Auto-Push
```

Die Config-Datei wird automatisch von den Python-Skripten gelesen. Werte können weiterhin per Environment-Variable überschrieben werden.

**Wichtige Config-Parameter:**

| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `test_case_limit` | (legacy) | Wird jetzt automatisch auf 1 gesetzt (Single Feature Focus) |
| `use_smart_test_limit` | (legacy) | Automatisch aktiv |
| `codex_model` | "" | LLM Model (z.B. "claude-sonnet-4.5") |
| `cycle_prompt_file` | coding_prompt.md | Prompt für Implementierungs-Cycles |
| `init_prompt_file` | init_prompt.md | Prompt für Initialisierung |
| `max_files` | (legacy) | Context wird jetzt dynamisch geladen |
| `max_file_bytes` | 200000 | Max Bytes pro Datei (für manuelle cats) |
| `sleep_secs` | 2 | Pause zwischen Cycles |
| `max_iterations` | 9999 | Max Anzahl Cycles |
| `max_errors` | 5 | Max Fehler bevor Stop |
| `cycle_timeout` | 1800 | Timeout pro Cycle (Sekunden) |
| `push_each_cycle` | 1 | Git Push nach Cycle (1=ja, 0=nein) |
| `git_remote` | origin | Git Remote Name |
| `log_level` | INFO | Log Level (DEBUG/INFO/WARNING/ERROR) |
| `stuck_threshold` | 5 | Stop wenn N Cycles ohne Fortschritt |
| `checkpoint_interval` | 10 | Git Tag alle N erfolgreichen Cycles |
| `validate_feature_list` | 1 | Validierung nach jedem Cycle |

### Legacy: Direkte Environment Variables

Alte Methode (funktioniert weiterhin):

### Legacy: Direkte Environment Variables

Alte Methode (funktioniert weiterhin):

**Prompt-Dateien:**
- `INIT_PROMPT_FILE` (Default: `init_prompt.md`)
- `CYCLE_PROMPT_FILE` (Default: `coding_prompt.md`)

Beispiele:
```bash
INIT_PROMPT_FILE=init_promt.md ./run_init.sh
CYCLE_PROMPT_FILE=coding_prompt.md ./run_cycle.sh
```

**run_until_green.sh:**
- `SLEEP_SECS` (Default: `2`)
- `MAX_ITERS` (Default: `9999`)
- `MAX_ERRORS` (Default: `5`)
- `LOG_DIR` (Default: `logs`)

Git Push (nach erfolgreichem Zyklus):
- `PUSH_EACH_CYCLE` (Default: `1`, setze `0` um Push zu deaktivieren)
- `GIT_REMOTE` (Default: `origin`)
- `GIT_BRANCH` (Default: leer = aktueller Branch)

Beispiele:
```bash
SLEEP_SECS=1 MAX_ERRORS=10 ./run_until_green.sh
PUSH_EACH_CYCLE=0 ./run_until_green.sh
```

---

## Troubleshooting

### 1) `ERROR: Prompt-Datei nicht gefunden`
- Ursache: `run_init.sh` oder `run_cycle.sh` findet die Prompt-Datei nicht.
- Lösung: Dateiname prüfen oder per Env-Var setzen:
  ```bash
  INIT_PROMPT_FILE=DEIN_INIT_PROMPT.md ./run_init.sh
  CYCLE_PROMPT_FILE=DEIN_CYCLE_PROMPT.md ./run_cycle.sh
  ```

### 2) `ERROR: app_spec.txt nicht gefunden im Projektroot.`
- Ursache: `run_init.sh` benötigt `app_spec.txt` im Projekt-Root.
- Lösung: Datei anlegen oder ins Root verschieben.

### 3) `ERROR: feature_list.json fehlt. Erst run_init.sh ausführen.`
- Ursache: Der Loop braucht `feature_list.json`.
- Lösung:
  ```bash
  ./run_init.sh
  ```

### 4) `ERROR: feature_list.json Format unbekannt`
- Ursache: Das JSON hat nicht das erwartete Format.
- Erwartet ist entweder:
  - `[...]` (Liste von Tests) oder
  - `{ "tests": [ ... ] }`
- Lösung: Format korrigieren oder neu baseline’n.

### 5) `ERROR: ssh-agent not available`
- Ursache: `push_each_cycle=1` ist gesetzt, aber kein `ssh-agent` verfügbar.
- Lösung Option 1 (ssh-agent starten):
  ```bash
  eval $(ssh-agent -s)
  ssh-add
  ```
- Lösung Option 2 (Push deaktivieren):
  In `harness.conf` setzen:
  ```
  push_each_cycle=0
  ```

### 6) Loop stoppt mit `STOP: error_count=... exceeded MAX_ERRORS=...`
- Ursache: Zu viele Fehler in `run_cycle.sh` oder beim optionalen Push.
- Lösung:
  - Log-Datei unter `logs/` öffnen (letzte Iteration).
  - `MAX_ERRORS` erhöhen und erneut starten:
    ```bash
    MAX_ERRORS=10 ./run_until_green.sh
    ```

### 7) `codex: command not found`
- Ursache: `codex` CLI ist nicht verfügbar.
- Lösung: `codex` korrekt installieren bzw. im `PATH` verfügbar machen.

---

## Erweiterte Features

### 1. Metrics & Progress Tracking

Das Harness sammelt automatisch Metriken über jeden Cycle:

```bash
# Metriken anzeigen
python3 scripts/metrics.py summary
```

Output:
```
📊 Harness Metrics Summary
━━━━━━━━━━━━━━━━━━━━━━━━
Total Cycles:         42
Successful Cycles:    38 (90.5%)
Total Tests Fixed:    187
Avg Cycle Duration:   845.3s
Error Rate:           0.095
Timeout Count:        2
```

Metriken werden in `harness_metrics.jsonl` gespeichert (JSONL Format für einfache Analyse).

### 2. Stuck Detection

Wenn mehrere Cycles in Folge keine Fortschritte machen (gleiche Tests fehlend), stoppt das Harness automatisch:

```bash
# In harness.conf
stuck_threshold=5  # Stop nach 5 Cycles ohne Fortschritt
```

Erkennbar an Logs wie:
```
[WARNING] No progress in last 3 cycles (same 5 tests failing)
[ERROR] Stuck detected: no progress in 5 cycles
```

### 3. Pause & Resume

Kontrolle während des Laufs ohne Abbruch:

```bash
# Pause (beendet aktuellen Cycle sauber, wartet dann)
touch .harness_pause

# Resume (Datei löschen)
rm .harness_pause

# Komplett stoppen nach aktuellem Cycle
touch .harness_stop
```

### 4. Checkpoints

Automatische Git Tags bei Meilensteinen:

```bash
# In harness.conf
checkpoint_interval=10  # Tag alle 10 erfolgreichen Cycles
```

Tags haben Format: `checkpoint-iter-50-passing-187`

Zurückkehren zu Checkpoint:
```bash
git tag | grep checkpoint
git checkout checkpoint-iter-40-passing-180
```

### 5. Prompt Versioning

Jeder Metric-Eintrag enthält einen Hash des `coding_prompt.md`:

```jsonl
{"iteration": 42, "prompt_version": "a3f2b91c", ...}
```

So kannst du nachvollziehen, welche Prompt-Version welche Ergebnisse lieferte.

### 6. Smart Context Injection (New v2)
Das Harness nutzt jetzt eine optimierte "Smart Context" Strategie, um Tokens zu sparen:
- Anstatt hunderte Dateien zu laden, bekommt der Agent nur die `app_spec.txt` und **genau einen fehlgeschlagenen Test**.
- Der Agent muss sich selbst Kontext beschaffen (via `ls`, `cat`), wenn er ihn braucht.
- Das garantiert vollen Fokus auf eine "Atomic Task".

### 7. Token Efficiency
Durch die Smart Context Strategie sinkt der Token-Verbrauch pro Cycle drastisch (oft < 2k Tokens für den Input), was längere Loops und geringere Kosten ermöglicht.
Die Config-Werte `max_files`, `max_git_log_lines` und `test_case_limit` sind in dieser Version obsolet, da der Context dynamisch minimal gebaut wird.

### 8. Structured Commit Messages

Der Prompt fordert strukturierte Commits:

```
[FIX] Authentication redirect loop

- Fixed session cookie persistence issue
- Updated login handler to check existing session
- Improved error messages for auth failures

Tests: 187 passing (+3 new), 15 failing (-3 fixed)
```

Types: `[FEAT]`, `[FIX]`, `[TEST]`, `[REFACTOR]`, `[DOCS]`

### 9. Smoke Tests

Vor dem ersten Cycle Umgebung prüfen:

```bash
chmod +x scripts/smoke_test.sh
./scripts/smoke_test.sh
```

Prüft:
- Erforderliche Commands (git, python3, codex)
- Dateien (feature_list.json, app_spec.txt)
- Git Repository Status
- Python Environment
- feature_list.json Format

### 10. Web Dashboard

Echtzeit-Monitoring via Browser:

```bash
python3 scripts/dashboard.py 8080
```

Öffne dann: http://localhost:8080

**Features:**
- 📊 Live Metrics (Cycles, Success Rate, Tests Fixed)
- 🎯 Test Progress (Pass/Fail Ratio mit Progress Bar)
- 📈 Recent Cycles (letzte 20 mit Status)
- 🏷️ Git History & Checkpoints
- 📝 Recent Log Files
- 🎮 Control Panel (Pause/Resume/Stop)
- 🔄 Auto-Refresh alle 5 Sekunden

**Control API:**
```bash
# Via curl (alternativ zu touch .harness_pause)
curl -X POST http://localhost:8080/api/control \
  -H "Content-Type: application/json" \
  -d '{"action": "pause"}'
```

---

## Sicherheitshinweis

Die Skripte starten den Agenten mit **`codex exec --yolo`** (ohne Sandbox/Landlock). Das bedeutet:
- Der Agent kann im Repo **beliebige Änderungen** vornehmen.
- Je nach Umgebung kann er auch **Befehle ausführen**, Dateien ändern/löschen, etc.

Empfehlungen:
- Arbeite in einer isolierten Umgebung (VM/Container/Separater User).
- Nutze Branches und reviewe Änderungen (`git diff`, `git log`) regelmäßig.
- Halte Secrets aus dem Repo heraus (z.B. keine API-Keys im Klartext).
- Verlasse dich auf den Git-Audit-Trail: häufig committen, klar benennen.

## Komplett Autonom
Damit das auch läuft wenn die shell Session abbricht
    ```bash
    nohup ./run_until_green.sh > codex.log 2>&1 &
     ```
