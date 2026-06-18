# Radar Classification (Technology Radar)

Definicja klasyfikacji komponentów na Technology Radar wg `classify_radar()`.

## Czwórka pierścieni (rings)

| Ring       | Ikona | Znaczenie                               | Kiedy przypisywany                                                |
| ---------- | ----- | --------------------------------------- | ----------------------------------------------------------------- |
| **adopt**  | 🟢    | Używamy, polecamy, gotowe do produkcji  | Komponent w `known_good` dla danego ekosystemu                    |
| **trial**  | 🔵    | Testujemy w ograniczonym zakresie       | DevDependency (npm) lub explicite w `trial`                       |
| **assess** | 🟡    | Obserwujemy, oceniamy użyteczność       | Domyślny dla library (npm/python) nie w known_good/known_outdated |
| **hold**   | 🔴    | Odchodzimy, nie polecamy nowych adopcji | Komponent w `known_outdated`                                      |

## Logika klasyfikacji

```python
for comp in components:
    name_lower = comp.name.lower()
    ecosystem_good = known_good.get(comp.ecosystem, [])
    ecosystem_old = known_outdated.get(comp.ecosystem, [])

    if name_lower in ecosystem_good:
        radar["adopt"].append(comp.name)
    elif name_lower in ecosystem_old:
        radar["hold"].append(comp.name)
    elif comp.type == "devDependency":
        radar["trial"].append(comp.name)
    else:
        radar["assess"].append(comp.name)
```

## Known Good (🟢 adopt) — per ekosystem

### Node.js

| Komponent    | Kategoria    | Uzasadnienie           |
| ------------ | ------------ | ---------------------- |
| `react`      | UI framework | Standard w frontendzie |
| `typescript` | Language     | Type safety standard   |
| `eslint`     | Linting      | Kod quality standard   |
| `prettier`   | Formatting   | Konsistentny styl      |
| `vitest`     | Testing      | Szybki, nowoczesny     |
| `jest`       | Testing      | Zdobywiony standard    |

### Python

| Komponent    | Kategoria       | Uzasadnienie                  |
| ------------ | --------------- | ----------------------------- |
| `fastapi`    | Web framework   | Nowoczesny, szybki, type-safe |
| `django`     | Web framework   | Baterie wliczone, dojrzały    |
| `flask`      | Micro-framework | Prosty, elastyczny            |
| `pytest`     | Testing         | Najpopularniejszy test runner |
| `pydantic`   | Validation      | Data validation + settings    |
| `sqlalchemy` | ORM             | Mocny, dojrzały ORM           |

## Known Outdated (🔴 hold) — per ekosystem

### Node.js

| Komponent   | Powód hold                             |
| ----------- | -------------------------------------- |
| `jquery`    | Zastąpione przez nowoczesne frameworki |
| `backbone`  | Legacy MV\*, nieutrzymywane            |
| `angularjs` | AngularJS 1.x EOL                      |
| `grunt`     | Zastąpione przez Vite/webpack/esbuild  |
| `gulp`      | Zastąpione przez Vite/webpack/esbuild  |

### Python

| Komponent   | Powód hold                                  |
| ----------- | ------------------------------------------- |
| `nose`      | Zastąpione przez pytest                     |
| `unittest2` | Backport unittest, niepotrzebny w py3       |
| `mock`      | W stdlib jako `unittest.mock` od py3.3      |
| `futures`   | W stdlib jako `concurrent.futures` od py3.2 |

## Rozszerzalność

Aby dodać/zmienić klasyfikację:

1. Edytuj `known_good` / `known_outdated` w `classify_radar()`
2. Zaktualizuj tę tabelę
3. Uruchom testy na znanych projektach

## Przykłady klasyfikacji

| Pakiet        | Typ           | Ecosystem | Ring      | Powód                                 |
| ------------- | ------------- | --------- | --------- | ------------------------------------- |
| `react`       | library       | node      | 🟢 adopt  | w known_good                          |
| `eslint`      | devDependency | node      | 🟢 adopt  | w known_good (ma priorytet nad trial) |
| `jest`        | devDependency | node      | 🟢 adopt  | w known_good                          |
| `lodash`      | library       | node      | 🟡 assess | domyślny                              |
| `jquery`      | library       | node      | 🔴 hold   | w known_outdated                      |
| `pytest`      | library       | python    | 🟢 adopt  | w known_good                          |
| `mock`        | library       | python    | 🔴 hold   | w known_outdated                      |
| `moje-wlasne` | library       | python    | 🟡 assess | domyślny                              |

---

_Wygenerowane z `inventory_scan.py::classify_radar()`_
