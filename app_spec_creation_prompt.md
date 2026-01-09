# Beispiel-Prompt: app_spec.txt erstellen lassen (für ChatGPT/Codex/LLM)

Du kannst den folgenden Prompt 1:1 in ein LLM kopieren und danach deine Stichpunkte einsetzen.

---

**PROMPT START**

Du bist ein erfahrener Product Owner + Solution Architect.
Erstelle eine Datei **app_spec.txt** als **vollständige, testbare Produktspezifikation**.

Vorgaben:
- Schreibe auf **Deutsch**.
- Nutze die folgenden Überschriften (halte die Struktur exakt ein).
- Die Spezifikation muss so konkret sein, dass daraus 200+ End-to-End-Tests abgeleitet werden können
  (User-Flows, UI, Validierungen, Edge Cases, Rollen/Rechte).
- Wenn Informationen fehlen, triff **plausible Annahmen** und markiere sie mit **[ANNAHME]**.
- Stelle **keine Rückfragen**, außer wenn es ohne Antwort unmöglich wäre, überhaupt einen sinnvollen Entwurf zu erstellen.

Struktur (bitte ausfüllen):
1) Überblick
2) Ziele und Nicht-Ziele
3) Rollen, Authentifizierung und Berechtigungen
4) Kern-User-Flows (End-to-End)
5) Funktionen (Functional Requirements)
6) UI/UX Anforderungen (Style Requirements)
7) Seiten / Routen / Navigation
8) Datenmodell
9) Backend / API (falls vorhanden)
10) Integrationen (optional)
11) Tech Stack & Lokales Setup (Install/Start-Kommandos, Ports/URLs)
12) Observability (optional)
13) Datenschutz/Sicherheit (optional)
14) Abnahmekriterien (Definition of Done)

Hier sind meine Stichpunkte (verwende sie als Quelle der Wahrheit):
- Produktname: [HIER EINSETZEN]
- Zielgruppe: [HIER EINSETZEN]
- Kurzbeschreibung: [HIER EINSETZEN]
- Must-have Features: [HIER EINSETZEN]
- UI/Design: [HIER EINSETZEN]
- Rollen/Rechte: [HIER EINSETZEN]
- Tech Stack Wunsch (falls vorhanden): [HIER EINSETZEN]
- Besondere Randfälle/Regeln: [HIER EINSETZEN]
- Out-of-scope: [HIER EINSETZEN]

Gib am Ende zusätzlich eine kurze Liste:
- „Offene Punkte / Annahmen“ (alles mit [ANNAHME])
- „3 nächste Schritte“, wie man die Spec weiter präzisiert.

**PROMPT END**
