# gzm_transport

Biblioteka Python do pobierania danych transportu publicznego GZM — dane statyczne GTFS + pozycje GPS i odjazdy na żywo z SDIP.

## Instalacja

```bash
pip install -e .
```

## Szybki start

```python
from gzm_transport import GZMTransport

with GZMTransport(gtfs_path="./gtfs_data") as gzm:
    # pobranie plików GTFS
    gzm.download_gtfs("./gtfs_data")

    # przystanki, linie
    stops = gzm.static.get_stops()
    lines = gzm.static.get_active_lines()
    katowice = gzm.static.search_stops("Katowice")

    # pozycje GPS pojazdów na żywo
    vehicles = gzm.live.fetch_vehicle_positions()

    # odjazdy z przystanku
    deps = gzm.live.fetch_stop_departures(stop_id=10001)

    # jako DataFrame
    df = gzm.vehicles_to_dataframe()
```

## API

### `GZMTransport(gtfs_path=".")`

Główny klient. Używaj jako context manager (`with`).

| Metoda | Zwraca |
|---|---|
| `download_gtfs(path)` | ścieżka do rozpakowanych plików |
| `get_all_vehicles()` | `list[VehiclePosition]` |
| `get_departures(stop_id)` | `list[Departure]` |
| `vehicles_to_dataframe()` | `pd.DataFrame` |
| `departures_to_dataframe(stop_id)` | `pd.DataFrame` |

### `StaticProvider` — dane GTFS

`get_stops()`, `get_routes()`, `get_trips()`, `get_stop_times()`, `get_calendar()`, `get_calendar_dates()`, `get_shapes()`, `get_agency()` — każda zwraca `pd.DataFrame`.

| Metoda | Opis |
|---|---|
| `download_gtfs(path)` | pobiera ZIP z otwartedane.metropoliagzm.pl |
| `search_stops(query)` | wyszukiwanie przystanków po nazwie |
| `get_stop_schedule(stop_id)` | rozkład jazdy dla przystanku |
| `get_active_lines()` | lista `[short_name, long_name]` |
| `available_files()` | pliki GTFS dostępne w katalogu |

### `LiveProvider` — dane SDIP na żywo

| Metoda | Zwraca |
|---|---|
| `fetch_vehicle_positions(line_type)` | `list[VehiclePosition]` |
| `fetch_stop_departures(stop_id)` | `list[Departure]` |
| `fetch_stop_info(stop_id)` | `StopInfo` lub `None` |

### Modele

- **`VehiclePosition`** — `timestamp`, `line_name`, `vehicle_id`, `direction`, `lat`, `lon`
- **`Departure`** — `timestamp`, `stop_id`, `line_name`, `destination`, `departure_time`, `is_live`
- **`StopInfo`** — `stop_id`, `name`, `lat`, `lon`

Każdy model ma `.to_dict()`.

## Testy

```bash
pip install -e ".[test]"
pytest tests/ -v
```

## Licencja

MIT
