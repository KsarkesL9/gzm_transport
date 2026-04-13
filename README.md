# gzm_transport

Biblioteka Python do pracy z danymi transportu publicznego GZM. Obsługuje pliki GTFS (rozkłady, przystanki) i dane na żywo z SDIP (pozycje GPS, odjazdy).

## Instalacja

```bash
pip install -e .
```

## Szybki start

```python
from gzm_transport import GZMTransport

with GZMTransport(gtfs_path="./gtfs_data") as gzm:
    # pobranie GTFS
    gzm.download_gtfs("./gtfs_data")

    # przystanki i linie
    stops = gzm.static.get_stops()
    lines = gzm.static.get_active_lines()
    katowice = gzm.static.search_stops("Katowice")

    # GPS na żywo — wszystkie pojazdy
    vehicles = gzm.live.fetch_vehicle_positions()

    # tylko tramwaje
    trams = gzm.live.fetch_vehicle_positions(line_type="tram")

    # odjazdy z przystanku
    deps = gzm.live.fetch_stop_departures(stop_id=10001)

    # to samo jako DataFrame
    df = gzm.vehicles_to_dataframe()
```

## API

### GZMTransport

Główny klient. Używaj jako context manager.

| Metoda | Co zwraca |
|---|---|
| `download_gtfs(path)` | ścieżka do plików |
| `get_all_vehicles()` | `list[VehiclePosition]` |
| `get_departures(stop_id)` | `list[Departure]` |
| `vehicles_to_dataframe()` | `DataFrame` |
| `departures_to_dataframe(stop_id)` | `DataFrame` |

### StaticProvider (GTFS)

`get_stops()`, `get_routes()`, `get_trips()`, `get_stop_times()`, `get_calendar()`, `get_calendar_dates()`, `get_shapes()`, `get_agency()` zwracają `DataFrame`.

Poza tym:
- `download_gtfs(path)` - pobiera ZIP z otwartedane.metropoliagzm.pl
- `search_stops(query)` - szukanie przystanków po nazwie
- `get_stop_schedule(stop_id)` - rozkład dla przystanku
- `get_active_lines()` - lista par `[short_name, long_name]`
- `available_files()` - jakie pliki GTFS są w katalogu

### LiveProvider (SDIP)

| Metoda | Co zwraca |
|---|---|
| `fetch_vehicle_positions(line_type)` | `list[VehiclePosition]` |
| `fetch_stop_departures(stop_id)` | `list[Departure]` |
| `fetch_stop_info(stop_id)` | `StopInfo` albo `None` |

`line_type` — filtrowanie pojazdów po typie. Domyślnie `"all"`.

| Wartość | Alias | Typ pojazdu |
|---|---|---|
| `"all"` | — | wszystkie |
| `"tram"` | `"t"`, `"0"` | tramwaje |
| `"bus"` | `"a"`, `"b"`, `"3"` | autobusy |
| `"trolleybus"` | `"trolejbus"`, `"11"` | trolejbusy |

### Modele

Wszystkie mają `.to_dict()`.

- `VehiclePosition` - timestamp, line_name, vehicle_id, direction, lat, lon
- `Departure` - timestamp, stop_id, line_name, destination, departure_time, is_live
- `StopInfo` - stop_id, name, lat, lon

## Testy

```bash
pip install -e ".[test]"
pytest tests/ -v
```

## Licencja

MIT
