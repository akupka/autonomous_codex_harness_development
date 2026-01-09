# Changelog - Autonomous Codex Harness

## Version 2.0 - Full Feature Implementation (Januar 2026)

### 🎯 Übersicht

Umfassende Verbesserung des Harness mit allen P0-P3 Features aus Verbesserungen.md implementiert.

### ✅ Implementierte Features

#### P0 - Kritische Verbesserungen
- **#1 SSH-Agent optional**: Nur noch erforderlich wenn `push_each_cycle=1`
- **#2 Feature List Validierung**: Automatische Validierung nach jedem Cycle
- **#3 Rollback-Strategie**: Automatischer Rollback bei Timeouts/Fehlern mit Backup-Tags
- **#5 Cycle Timeout**: Konfigurierbarer Timeout mit automatischem Rollback

#### P1 - Wichtige Verbesserungen
- **#4 Progress Metrics**: JSONL-basiertes Tracking mit `scripts/metrics.py`
- **#9 Smoke Tests**: Umfassende Environment-Prüfung vor Start

#### P2 - Performance & Qualität
- **#6 Context Size Optimization**: Intelligente Datei-Priorisierung nach Relevanz
- **#7 Stuck Detection**: Automatischer Stop bei fehlenden Fortschritten
- **#8 Commit Messages**: Strukturierte Commit-Templates im Prompt
- **#14 Prompt Versioning**: Hash-Tracking für Prompt-Änderungen

#### P3 - Benutzerfreundlichkeit
- **#10 Smart Test Limit**: Dynamische Test-Anzahl basierend auf Fehlern
- **#11 Log Levels**: DEBUG/INFO/WARNING/ERROR mit Filterung
- **#12 Pause/Resume**: `.harness_pause` und `.harness_stop` Control Files
- **#16 Checkpoints**: Automatische Git Tags alle N Iterationen

#### P4 - Monitoring & Visualization
- **#13 Dashboard**: Web-basiertes Real-time Monitoring mit Control Panel

### 📝 Geänderte Dateien

#### Neue Dateien
- `scripts/metrics.py` - Metriken-Sammlung mit CLI
- `scripts/smoke_test.sh` - Environment-Checks
- `scripts/dashboard.py` - Web Dashboard Server
- `CHANGELOG.md` - Diese Datei
- `harness_metrics.jsonl` - Metriken-Speicher (wird generiert)

#### Erweiterte/Überarbeitete Dateien
- `run_until_green.sh` - +200 Zeilen: Metrics, Stuck Detection, Logging, Pause/Resume, Checkpoints
- `scripts/context_builder.py` - Smart Prioritization, Smart Test Limit
- `scripts/config.py` - Neue Config-Parameter
- `coding_prompt.md` - Commit Message Templates
- `harness.conf` - Neue Parameter (log_level, stuck_threshold, checkpoint_interval, etc.)
- `README.md` - Dokumentation aller neuen Features
- `Anleitung.md` - Erweiterte Tipps und Tricks
- `Verbesserungen.md` - Status-Update aller Implementierungen

### 🔧 Neue Konfigurationsoptionen

```bash
# harness.conf - Neue Parameter
log_level=INFO                    # DEBUG/INFO/WARNING/ERROR
stuck_threshold=5                 # Stop nach N Cycles ohne Fortschritt
checkpoint_interval=10            # Git Tag alle N Cycles
use_smart_test_limit=1            # Dynamische Test-Anzahl
validate_feature_list=1           # Validierung nach Cycle
```

### 📊 Neue CLI Commands

```bash
# Metriken anzeigen
python3 scripts/metrics.py summary

# Metriken erfassen (intern von run_until_green.sh)
python3 scripts/metrics.py record <iteration> <duration> <success> <failing_before> <failing_after> [error] [timeout] [prompt_hash]

# Environment prüfen
./scripts/smoke_test.sh
```

### 🎮 Neue Control-Mechanismen

```bash
# Pause nach aktuellem Cycle
touch .harness_pause

# Resume
rm .harness_pause

# Stop nach aktuellem Cycle
touch .harness_stop
```

### 📈 Metriken & Tracking

Jeder Cycle wird jetzt getrackt:
- Zeitstempel
- Iteration Nr.
- Dauer (Sekunden)
- Erfolg/Fehler
- Tests vorher/nachher
- Fortschritt
- Error Message
- Timeout Flag
- Prompt Version Hash

### 🏷️ Checkpoint System

Automatische Git Tags bei Meilensteinen:
```
checkpoint-iter-10-passing-45
checkpoint-iter-20-passing-89
checkpoint-iter-30-passing-142
```

### 🔍 Stuck Detection

Trackt die letzten N Cycles:
- Wenn gleiche Tests N mal hintereinander fehlschlagen → Stop
- Logs: `[WARNING] No progress in last X cycles`
- Verhindert endlose Loops

### 📋 Smart Test Limit

Passt Test-Anzahl dynamisch an:
- **≤3 fehlerhafte Tests**: Zeige bis zu 15 Tests (mehr Context)
- **Viele fehlerhafte Tests**: Limitiere auf `test_case_limit`
- Optimiert Token-Nutzung

### 🎯 Context Prioritization

Dateien werden nach Relevanz sortiert:
- **High Priority** (+100): `.json`, `.md`, `.txt`
- **Medium Priority** (+50): Code-Dateien
- **Low Priority** (+10): Styling/Config
- **Test Match** (+200): Dateiname in failing Test erwähnt

### 🛡️ Robustheit

- Automatischer Rollback bei Timeout/Fehler
- Backup-Commits mit Tags: `failed-cycle-X-backup`
- Validierung der feature_list.json nach jedem Cycle
- Graceful Handling von Control Files

### 📚 Dokumentation

Alle Dokumente aktualisiert:
- README.md: Technische Referenz mit allen Features
- Anleitung.md: Schritt-für-Schritt Guide mit Beispielen
- Verbesserungen.md: Implementation Status Tracking
- harness.conf: Inline-Kommentare für alle Parameter

### ❌ Nicht Implementiert (P4 - Low Priority)

- **#13 Dashboard**: Web UI für Monitoring (zu aufwändig)
- **#15 Parallel Tests**: Parallele Test-Ausführung (komplex, niedriger ROI)

### 🔮 Breaking Changes

Keine Breaking Changes! Alle bestehenden Skripte funktionieren weiterhin.

### 🚀 Migration

Keine Migration nötig. Neue Features sind optional und aktivieren sich automatisch via Config.

### 📊 Statistik

- **+1000 Zeilen Code** (Bash + Python + HTML/CSS/JS)
- **16 neue Features** implementiert
- **5 neue Dateien** erstellt
- **8 Dateien** erweitert
- **3 Dokumentations-Dateien** überarbeitet

### 🙏 Credits

Implementiert nach Analyse und Planung in Verbesserungen.md.

---

## Version 1.0 - Initial Release

Basis-Funktionalität:
- run_init.sh - Projekt-Initialisierung
- run_cycle.sh - Einzelner Dev-Cycle
- run_until_green.sh - Loop bis alle Tests grün
- scripts/context_builder.py - Context-Assembly
- scripts/config.py - Config-Loading
- Zentrale harness.conf Konfiguration
