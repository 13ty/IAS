# Port Conflict Detection

Wykrywanie konfliktów portów między narzędziami.

## Metoda

1. Parsowanie `run_command` regexem `[:\s](\d{4,5})`
2. Porównanie z portami z `.envy`
3. Wykrywanie konfliktów (ten sam port = wiele narzędzi)

```python
PORT_PATTERN = re.compile(r"[:\s](\d{4,5})")

def detect_port_conflicts(tools: List[ToolInfo], envy_ports: List[int]) -> List[PortConflict]:
    tool_ports = {}

    for tool in tools:
        matches = PORT_PATTERN.findall(tool.run_command)
        for port_str in matches:
            port = int(port_str)
            if port not in tool_ports:
                tool_ports[port] = []
            tool_ports[port].append(tool.id)

    conflicts = []
    for port, tool_ids in tool_ports.items():
        if len(tool_ids) > 1:
            conflicts.append(PortConflict(
                port=port,
                tools=tool_ids,
                severity="high"
            ))
        elif port in envy_ports:
            conflicts.append(PortConflict(
                port=port,
                tools=tool_ids,
                severity="medium"
            ))

    return conflicts
```

## Przykłady

| Port | Narzędzia    | Źródło      | Severity    |
| ---- | ------------ | ----------- | ----------- |
| 6542 | LanceDB      | .envy       | ℹ️ Info     |
| 1234 | LMStudio     | .envy       | ℹ️ Info     |
| 8080 | tool1, tool2 | run_command | 🔴 Conflict |

## Severity Levels

| Level      | Opis                              | Akcja         |
| ---------- | --------------------------------- | ------------- |
| **high**   | Wiele narzędzi na jednym porcie   | Pilna naprawa |
| **medium** | Narzędzie używające portu z .envy | Monitoruj     |
| **low**    | Pojedyncze narzędzie, port wolny  | Brak działań  |

## Ignorowane porty

| Port | Powód             |
| ---- | ----------------- |
| 0    | Random port       |
| 80   | HTTP default      |
| 443  | HTTPS default     |
| 3000 | Common dev server |
| 8080 | Common alt HTTP   |

## Rozszerzalność

| Nowa metryka         | Co mierzy                   | Jak                          |
| -------------------- | --------------------------- | ---------------------------- |
| **Port utilization** | Ile portów jest używanych   | used_ports / available_ports |
| **Port density**     | Średnia narzędzi per port   | total_tools / used_ports     |
| **Port range**       | Rozpiętość używanych portów | max(port) - min(port)        |
