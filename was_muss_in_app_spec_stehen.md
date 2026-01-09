# Was muss in app_spec.txt mindestens drinstehen?

Damit dein Harness sauber funktioniert, braucht die Spec genug Informationen, damit der Initializer daraus (a) feature_list.json und (b) ein brauchbares init.sh erzeugen kann. Der Initializer ist explizit darauf ausgelegt, zuerst app_spec.txt zu lesen und daraus 200+ E2E-Tests abzuleiten. Außerdem bricht run_init.sh ab, wenn app_spec.txt fehlt. 


## Pflichtinhalte (Minimum)

- Kurzbeschreibung & Ziel
  Was ist die App und wozu dient sie?
- Kern-User-Flows (E2E)
  2–5 zentrale Abläufe in Schrittform (Login → Aktion → Ergebnis). Das ist die Basis für Tests.
- Rollen & Rechte
  Mindestens: Wer darf was? (auch wenn es nur „User“ gibt).
- Functional Requirements
  Must-haves + wichtigste Validierungen und Fehlerfälle.
- UI/UX Anforderungen
  Was ist „style-relevant“? (Responsiveness, Kontrast, Zustände wie Loading/Empty/Error, keine Console Errors etc.)
- Tech Stack & Local Run
  Sehr wichtig, weil daraus init.sh gebaut wird:
  * Welche Technologien (Frontend/Backend/DB)?
  * Wie installiert man Dependencies?
  * Wie startet man lokal? Welche Ports/URLs?

Der Coding-Agent liest app_spec.txt bei jedem Zyklus als Referenz und orientiert sich zusätzlich an feature_list.json. Wenn die Spec zu dünn ist, wird die Testliste zwangsläufig voller Annahmen oder unpräzise.
