# IAS — Architektura modułowa (ustalenia 2026-06-23)

## Problem

Projekt IAS ma pomieszane odpowiedzialności. Kwatermistrz w kodzie i dokumentacji
robi "wszystko" — skanuje, zbiera URL-e, ocenia, rejestruje, generuje heatmapę.
Przez to żadna z tych funkcji nie działa dobrze.

Konkretnie:

- tool_registry.json ma 18 wpisów. scan_environment.py (856 linii) istnieje i skanuje
  rejestr Windows, PATH, menedżery pakietów, R:\Dev\Tools — ale nie został
  uruchomiony do końca. Miało być ~2000 wpisów.
- proposals.csv (~150 wpisów) leży obok, nikt nie porównuje go z heatmapą.
- Nikt nie wie co jest czym i kto za co odpowiada.

## Moduły

### IaSpedition — dostarczanie danych

Przyjmuje surowy materiał z różnych źródeł i dostarcza w odpowiednie miejsce
z adnotacją "skąd" i "po co".

Źródła:

- GitHub URL-e (ręczne wrzuty, "popatrz na ten interface")
- Browser history (automatyczne zbieranie)
- Scout (aktywne szukanie przez gh CLI)
- Ręczne (agent w trakcie pracy)
- Batch scan środowiska (scan_environment.py)

Przeznaczenie (adnotacja, nie decyzja):

- do oceny
- do nauki
- do przejrzenia
- do archiwum

IaSpedition nie ocenia. Tylko dostarcza.

### IaStorage — składowanie ze stanem

Przechowuje dane o repozytoriach. Każdy wpis ma stan:

- surowy / przetworzony / zweryfikowany / zdezaktualizowany
- kto i kiedy dodał
- gdzie jest w procesie

Operacje: odczyt, zapis, zmiana stanu.

IaStorage nie ocenia. Tylko trzyma i informuje o stanie.

### IAStrategist / IASpiratio — ewaluacja, wyszukiwanie, porównywanie

Serce decyzyjne. Ma zdefiniowane schematy oceny:

- 4D taksonomia (Layer A, Function B, Domain C, Pattern D)
- Skąd się biorą? Z naszych potrzeb i z heatmapy Kwatermistrza

Porównuje:

- kandydata z tym co mamy (tool_registry Kwatermistrza)
- kandydata z tym czego potrzebujemy (gaps z heatmapy)

Każda ocena ma termin ważności — repo może umrzeć, zmienić licencję,
być porzucone. Po terminie ocena wygasa.

Decyzje:

- ADOPT — nie mamy, potrzebujemy, dodajemy
- MIGRUJ — mamy gorsze, zastępujemy
- HOLD — może kiedyś, zapisujemy z datą ważności
- REJECT — niepotrzebne / gorsze / nieaktualne

### Kwatermistrz — magazynier istniejącego stanu

Jest ostatni, nie pierwszy. Nie zbiera, nie ocenia, nie decyduje.

Robi:

- Wie CO MAMY (tool_registry.json, docelowo ~2000 wpisów)
- Pokazuje heatmapę (luki, nakładania, konflikty portów)
- Odpowiada "gdzie jest X", "jak odpalić Y"
- Może wskazać kierunek: "mamy braki, sprawdź IaStorage,
  albo zleć IaSpedition szukanie"

Nie robi:

- nie zbiera URL-i z Githuba
- nie ocenia nowych repozytoriów
- nie mówi "zainstaluj X"

## Przepływ danych

IaSpedition → IaStorage → IAStrategist → Kwatermistrz

Kwatermistrz jest na końcu. Dostaje gotowe dane, aktualizuje stan,
pokazuje gdzie jesteśmy.

## Stan obecny kodu

Co istnieje i do którego modułu pasuje:

| Moduł        | Istniejący kod                                   | Stan                                   |
| ------------ | ------------------------------------------------ | -------------------------------------- |
| IaSpedition  | proposal_collect.py, scout_search.py             | Są, ale nie połączone w pipeline       |
| IaSpedition  | scan_environment.py                              | 856 linii, NIEURUCHOMIONY              |
| IaStorage    | state/repo_queue.json, state/repo_knowledge.json | Są, ale nie wiadomo który jest aktywny |
| IAStrategist | proposal_audit.py, analyzer_check.py             | Są, ale nie porównują z heatmapą       |
| Kwatermistrz | tool_registry.json, heatmap.py, mcp_server.py    | 18 wpisów zamiast ~2000                |
| IASparta     | graph.py, search.py, embeddings.py               | Działa, odizolowany                    |
