# Anleitung: Autonomous Codex Harness

Willkommen! Diese Anleitung zeigt dir Schritt für Schritt, wie du den **Autonomous Codex Harness** für deine Projekte nutzt.

---

## 📦 Teil 1: Harness von GitHub herunterladen

### Option A: Als Vorlage für ein neues Projekt (empfohlen)

Wenn du ein **neues Projekt** starten möchtest:

```bash
# 1. Neues Verzeichnis für dein Projekt anlegen
mkdir mein-neues-projekt
cd mein-neues-projekt

# 2. Git Repository initialisieren
git init

# 3. Harness-Files von GitHub holen (ohne die History)
curl -L https://github.com/akupka/autonomous_codex/archive/refs/heads/main.tar.gz | tar xz --strip=1

# 4. Eigenes Remote-Repository verbinden
git remote add origin https://github.com/DEIN_USERNAME/DEIN_PROJEKT.git

# 5. Ersten Commit machen
git add .
git commit -m "Initial project setup with Autonomous Codex Harness"
git branch -M main
git push -u origin main
```

### Option B: Zum Experimentieren klonen

Wenn du erst **experimentieren** möchtest:

```bash
# Komplettes Repository klonen
git clone https://github.com/akupka/autonomous_codex.git
cd autonomous_codex

# Zum Experimentieren eigenen Branch anlegen
git checkout -b experiment
```

---

## 🎯 Teil 2: Neues Projekt mit dem Harness anlegen

### Schritt 1: Projektordner vorbereiten

Wenn du Option A oben genutzt hast, bist du schon im richtigen Verzeichnis. Ansonsten:

```bash
mkdir mein-projekt
cd mein-projekt
# ... Harness-Files hierher kopieren (siehe Option A)
```

### Schritt 2: Konfiguration anpassen

**Für kleine Projekte (20-50 Tests):**
```bash
cp harness.conf.small-project harness.conf
```

**Für große Projekte (200+ Tests):**
```bash
cp harness.conf.large-project harness.conf
```

**Oder manuell bearbeiten:**
```bash
# harness.conf erstellen und anpassen:
cat > harness.conf << 'EOF'
test_case_limit=50
push_each_cycle=0
max_errors=10
cycle_timeout=1800
EOF
```

**Wichtige Config-Parameter:**
- `test_case_limit`: (Legacy) Wird jetzt automatisch auf 1 gesetzt, da der Agent immer nur einen Test pro Cycle bearbeitet.
- `push_each_cycle`: `0` = kein Auto-Push (gut für Entwicklung), `1` = Auto-Push nach jedem Cycle
- `max_errors`: Wie viele Fehler toleriert werden bevor Stop
- `cycle_timeout`: Max. Dauer eines Cycles in Sekunden (1800 = 30 Min)

### Schritt 3: `app_spec.txt` schreiben

Erstelle eine Datei `app_spec.txt` mit deinen Projektanforderungen. Nutze die Vorlage:

```bash
# Optional: Vorlage als Ausgangspunkt nutzen
cp app_spec_template.txt app_spec.txt
```

**Wichtig:** Die `app_spec.txt` sollte so konkret sein, dass daraus End-to-End-Tests abgeleitet werden können:
- Beschreibe User-Flows detailliert
- Definiere UI/UX-Anforderungen klar
- Spezifiziere Validierungen und Edge Cases
- Gib Tech Stack an

**Beispiel-Struktur:**
```
# Projekt: Meine Todo-App

## Überblick
Eine einfache Todo-Listen App mit Drag & Drop...

## Kern-User-Flows
FLOW-01: Nutzer kann Todo erstellen
- Step 1: Öffne / 
- Step 2: Klicke "Neues Todo"
- Step 3: Gib Text ein...

## Funktionen
FEAT-01: Todos anlegen, bearbeiten, löschen
FEAT-02: Drag & Drop zum Sortieren
...

## UI/UX Anforderungen
UI-01: Buttons haben min. 44×44px Touch-Target
UI-02: Farbkontrast min. 4.5:1
...

## Tech Stack
- Frontend: React + TypeScript
- Backend: Node.js + Express
- Database: SQLite
- Port: localhost:3000
```

### Schritt 4: Initializer starten (Baseline erstellen)

Der Initializer erstellt:
- `feature_list.json` (umfangreicher Testkatalog basierend auf deiner Spec)
- `init.sh` (Setup-Script für die Entwicklungsumgebung)
- Erste Git-Commits

```bash
chmod +x run_init.sh
./run_init.sh
```

**Was passiert:**
- Codex liest deine `app_spec.txt`
- Erstellt 200 detaillierte End-to-End-Tests in `feature_list.json`
- Generiert `init.sh` für Environment-Setup
- Macht ersten Git-Commit

**Nach dem Init hast du:**
- ✅ `feature_list.json` mit allen Tests (alle auf `"passes": false`)
- ✅ `init.sh` zum Starten der Umgebung
- ✅ Git History mit Baseline
- ✅ Evtl. erste Projektstruktur (Ordner, Dateien)

### Schritt 5: Entwicklungsumgebung starten

```bash
chmod +x init.sh
./init.sh
```

Das Script:
- Installiert Dependencies (npm/pip/etc.)
- Startet Server/Datenbank
- Zeigt dir, wie du die App erreichst (z.B. http://localhost:3000)

**Tipp:** Lass das Terminal mit `init.sh` offen (Server läuft). Öffne ein zweites Terminal für die nächsten Schritte.

### Schritt 6: Smoke Tests durchführen (optional aber empfohlen)

Prüfe, ob alles bereit ist:

```bash
./scripts/smoke_test.sh
```

Das Script checkt:
- ✅ Alle benötigten Tools (git, python3, codex)
- ✅ Erforderliche Dateien vorhanden
- ✅ feature_list.json ist valide
- ✅ Git Repository OK
- ⚠️ Server läuft (optional)

### Schritt 7: SSH-Agent einrichten (für Auto-Push)

**Nur nötig wenn `push_each_cycle=1` in `harness.conf`:**

```bash
eval $(ssh-agent -s)
ssh-add
```

**Wenn du `push_each_cycle=0` gesetzt hast, kannst du diesen Schritt überspringen.**

### Schritt 8: Autonomen Loop starten ("until green")

```bash
chmod +x run_cycle.sh run_until_green.sh
./run_until_green.sh
```

**Was passiert:**
1. Der Agent sucht sich den nächsten Test mit `"passes": false`
2. Implementiert das Feature
3. Verifiziert über die UI (Browser-Automatisierung)
4. Markiert Test als `"passes": true` wenn erfolgreich
5. Macht Git-Commit
6. Wiederholt, bis alle Tests grün sind

**Logs:** Alle Cycles werden in `logs/` gespeichert.

**Stoppen:**
- `Ctrl+C` für sofortigen Stop
- Oder: `touch .harness_pause` in anderem Terminal → pausiert nach aktuellem Cycle
- Oder: `touch .harness_stop` → stoppt graceful nach aktuellem Cycle

### Schritt 9: Fortschritt überwachen

Während der Loop läuft:

```bash
# In anderem Terminal:
# Wie viele Tests sind noch offen?
grep '"passes": false' feature_list.json | wc -l

# Letztes Log anschauen:
tail -f logs/cycle_*.log | tail -100

# Git History:
git log --oneline -20

# Progress Notes:
cat codex-progress.txt
```

---

## 🔄 Teil 3: Projekt erweitern / Weiterarbeiten

### Normalbetrieb: Spec bleibt gleich

Wenn du am nächsten Tag weiterarbeiten willst:

```bash
# 1. Umgebung starten (falls noch nicht läuft)
./init.sh

# 2. Loop starten (macht da weiter wo er aufgehört hat)
./run_until_green.sh
```

### Spec-Änderungen: Neue Features hinzufügen

Wenn sich Anforderungen in `app_spec.txt` ändern:

#### Option A: Nur additive Änderungen (neue Features dazu)

Neue Tests manuell zu `feature_list.json` hinzufügen:

```json
{
  "category": "functional",
  "description": "FLOW-99: Neues Feature XY",
  "steps": ["Step 1: ...", "Step 2: ..."],
  "passes": false
}
```

#### Option B: Größere Änderungen (Re-Baseline)

Wenn Features sich grundlegend ändern:

```bash
# 1. Checkpoint vor Änderung
git add -A
git commit -m "Checkpoint before spec change"
git tag spec-v1-baseline

# 2. app_spec.txt anpassen
nano app_spec.txt
git add app_spec.txt
git commit -m "Update spec to v2"

# 3. Alte feature_list archivieren
cp feature_list.json feature_list.v1.json
git add feature_list.v1.json
git commit -m "Archive feature_list v1"

# 4. Neue feature_list.json generieren lassen
# (Nutze spec_update_prompt.md oder ähnlich)
CYCLE_PROMPT_FILE=spec_update_prompt.md ./run_cycle.sh

# 5. Rebaseline committen
git add feature_list.json
git commit -m "Rebaseline feature_list to spec v2"
git tag spec-v2-baseline

# 6. Normal weitermachen
./run_until_green.sh
```

---

## 🛠️ Teil 4: Troubleshooting

### Problem: "ERROR: Required command not found: codex"

**Lösung:** Installiere den Codex CLI:
```bash
# Installationsanleitung für codex:
# https://github.com/... (je nach deiner Codex-Version)
```

### Problem: "ERROR: app_spec.txt nicht gefunden"

**Lösung:** Du bist im falschen Verzeichnis oder die Datei fehlt:
```bash
pwd  # Bist du im Projektordner?
ls -la app_spec.txt  # Existiert die Datei?
```

### Problem: "ERROR: feature_list.json fehlt"

**Lösung:** Du hast den Init-Schritt übersprungen:
```bash
./run_init.sh
```

### Problem: "ERROR: ssh-agent not available"

**Lösung:** Entweder ssh-agent starten:
```bash
eval $(ssh-agent -s)
ssh-add
```

**Oder** in `harness.conf` setzen:
```
push_each_cycle=0
```

### Problem: Tests schlagen immer wieder fehl

**Lösung:**
```bash
# 1. Letztes Log anschauen
cat logs/cycle_*_*.log | tail -100

# 2. Manuell testen
# Starte die App und teste den failing test manuell

# 3. Falls Agent "stuck" ist:
# - Stop mit Ctrl+C
# - Manuell fixen
# - Test in feature_list.json auf "passes": true setzen
# - Committen
# - Weitermachen mit ./run_until_green.sh
```

### Problem: Cycle dauert ewig

**Lösung:** Timeout ist zu hoch, in `harness.conf` anpassen:
```
cycle_timeout=900  # 15 Minuten
```

### Problem: Agent findet Dateien nicht
**Lösung:** Da der Agent in der neuen "Smart Context" Version nur minimalen Kontext erhält, muss er Dateien explizit lesen (`cat`). Wenn er halluziniert oder Dateien nicht findet:
- Prüfe, ob die Dateipfade im Prompt korrekt sind
- Ergänze im `coding_prompt.md` den Hinweis: "Use `ls -R` to find files if unsure."

---

## 📊 Teil 5: Best Practices

### ✅ Do's

1. **Klare Specs schreiben:** Je präziser `app_spec.txt`, desto besser die Tests
2. **Häufig committen:** Git ist dein Audit-Trail
3. **Logs reviewen:** Nach jedem paar Cycles mal `git log` und `git diff` anschauen
4. **Kleine Iterationen:** Lieber 50 Tests perfekt als 200 halb fertig
5. **Config anpassen:** `harness.conf` ist dein Freund - nutze sie!

### ❌ Don'ts

1. **Tests nicht manuell löschen:** Sonst verlierst du Features
2. **Keine direkten Code-Edits während Loop läuft:** Agent und du edieren gleichzeitig = Konflikt
3. **feature_list.json nicht per Hand umbauen:** Nur `"passes"` Feld ändern!
4. **Nicht ohne Backup experimentieren:** Git tags nutzen!

### 💡 Tipps

- **Pause einlegen:** `touch .harness_pause` → Agent pausiert
- **Checkpoints setzen:** Nach jedem Meilenstein `git tag v0.1`, `git tag v0.2` etc.
- **Monitoring:** Entwickle ein Gefühl dafür, wie lange ein Cycle dauert (normal: 5-20 Min)
- **Parallel arbeiten:** Während Agent läuft, kannst du Doku schreiben, Designs machen, etc.

---

## 🎓 Teil 6: Erweiterte Nutzung

### Custom Prompts

Eigene Prompts für spezielle Zwecke:

```bash
# Custom Init-Prompt:
INIT_PROMPT_FILE=my_custom_init.md ./run_init.sh

# Custom Cycle-Prompt:
CYCLE_PROMPT_FILE=my_special_prompt.md ./run_cycle.sh
```

### Nur einen Cycle starten (ohne Loop)

```bash
./run_cycle.sh  # Führt genau einen Cycle aus und stoppt
```

### Config-Werte überschreiben

Environment Variables haben Vorrang vor `harness.conf`:

```bash
MAX_ERRORS=20 CYCLE_TIMEOUT=3600 ./run_until_green.sh
```

### Im Hintergrund laufen lassen

```bash
nohup ./run_until_green.sh > codex.log 2>&1 &

# Status checken:
tail -f codex.log

# Pause einlegen (graceful):
touch .harness_pause

# Wieder fortsetzen:
rm .harness_pause

# Stoppen nach aktuellem Cycle:
touch .harness_stop

# Sofort beenden:
killall run_until_green.sh
```

---

## 🚀 Erweiterte Features

### Metriken anzeigen

```bash
python3 scripts/metrics.py summary
```

Zeigt:
- Anzahl erfolgreicher/fehlgeschlagener Cycles
- Durchschnittliche Cycle-Dauer
- Insgesamt behobene Tests
- Timeout-Rate

### Checkpoints nutzen

```bash
# Alle Checkpoints anzeigen
git tag | grep checkpoint

# Zu Checkpoint zurückkehren
git checkout checkpoint-iter-50-passing-187

# Wieder auf main
git checkout main
```

### Stuck Detection

Wenn mehrere Cycles keine Fortschritte machen, stoppt das Harness automatisch:

```
[WARNING] No progress in last 3 cycles
[ERROR] Stuck detected: no progress in 5 cycles
```

Dann:
1. Logs prüfen: Was blockiert?
2. Prompt anpassen (evtl. spezifischere Anweisungen)
3. `coding_prompt.md` committen (neue Prompt-Version)
4. Erneut starten

### Log Levels anpassen

In `harness.conf`:
```bash
log_level=DEBUG  # Sehr ausführlich
log_level=INFO   # Normal (empfohlen)
log_level=WARNING  # Nur Warnungen
log_level=ERROR  # Nur Fehler
```

### Dashboard starten

Für visuelles Monitoring im Browser:

```bash
# In neuem Terminal
python3 scripts/dashboard.py 8080

# Browser öffnen
xdg-open http://localhost:8080  # Linux
# oder: open http://localhost:8080  # macOS
```

Dashboard zeigt live:
- Test Progress (Pass/Fail)
- Cycle Metrics & History
- Git Checkpoints
- Control Panel (Pause/Resume/Stop)

---

## 📚 Weitere Ressourcen

- **README.md** – Technische Details, alle Features
- **Verbesserungen.md** – Liste implementierter Verbesserungen
- **harness.conf** – Alle Config-Optionen mit Kommentaren
- **coding_prompt.md** – Der Prompt, den der Agent verwendet
- **init_prompt.md** – Der Initializer-Prompt
- **scripts/smoke_test.sh** – Umgebungsprüfung
- **scripts/metrics.py** – Metriken-Sammlung und Analyse

---

## 💬 Fragen?

Bei Problemen:
1. Smoke Tests laufen lassen: `./scripts/smoke_test.sh`
2. Logs checken: `ls -lth logs/ | head`
3. Git Status: `git status`, `git log --oneline -10`
4. Config checken: `cat harness.conf`
5. Metriken: `python3 scripts/metrics.py summary`

**Viel Erfolg mit deinem Projekt! 🚀**
