from __future__ import annotations

from bs4 import BeautifulSoup
from .models import VehiclePosition, Departure, StopInfo
from datetime import datetime
import logging
import time

LINE_TYPE_MAP = {
    "all": "all",
    "tram": "0", "t": "0", "0": "0",
    "bus": "3", "a": "3", "b": "3", "3": "3",
    "trolleybus": "11", "trolejbus": "11", "11": "11",
}


class LiveProvider:

    def __init__(self, session, base_url: str, retries: int = 2):
        self.session = session
        self.base_url = base_url
        self.retries = retries
        self.logger = logging.getLogger(__name__)

    def _get(self, params: dict, timeout: int = 15):
        last_exc = None
        for attempt in range(1 + self.retries):
            try:
                r = self.session.get(self.base_url, params=params, timeout=timeout)
                r.raise_for_status()
                return r
            except Exception as e:
                last_exc = e
                if attempt < self.retries:
                    time.sleep(1 * (attempt + 1))
        raise last_exc

    def fetch_vehicle_positions(self, line_type: str = "all") -> list[VehiclePosition]:
        lt_value = LINE_TYPE_MAP.get(line_type.lower(), line_type)
        params = {"command": "planner", "action": "v", "lt": lt_value}
        try:
            r = self._get(params)
            data = r.json()
            now = datetime.now().isoformat()

            positions: list[VehiclePosition] = []
            for v in data:
                lat = float(v.get("lat", 0))
                lon = float(v.get("lon", 0))

                positions.append(
                    VehiclePosition(
                        timestamp=now,
                        line_name=str(v.get("lineLabel", "")),
                        vehicle_id=str(v.get("id", "")),
                        direction=v.get("trip", ""),
                        lat=lat,
                        lon=lon,
                    )
                )
            return positions

        except Exception as e:
            self.logger.error("GPS Stream Error: %s", e)
            return []

    fetch_gps_stream = fetch_vehicle_positions

    def fetch_stop_departures(self, stop_id: int) -> list[Departure]:
        params = {"command": "planner", "action": "sd", "id": stop_id}
        try:
            r = self._get(params)
            soup = BeautifulSoup(r.text, "html.parser")
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            deps: list[Departure] = []
            for row in soup.find_all("div", class_="departure"):
                line_el = row.find("div", class_="line")
                dest_el = row.find("div", class_="destination")
                time_el = row.find("div", class_="time")

                if not (line_el and dest_el and time_el):
                    continue

                time_text = time_el.get_text(strip=True)
                # status-1 = pojazd na przystanku (>>>)
                # "min" w czasie = prognoza GPS (np. "4 min")
                # ">>>" = pojazd dojeżdża/na przystanku
                # Czas w formacie HH:MM bez powyższych = dane rozkładowe
                is_live = (
                    "status-1" in row.get("class", [])
                    or "min" in time_text.lower()
                    or ">>>" in time_text
                )

                deps.append(
                    Departure(
                        timestamp=now,
                        stop_id=stop_id,
                        line_name=line_el.get_text(strip=True),
                        destination=dest_el.get("title", dest_el.get_text(strip=True)),
                        departure_time=time_el.get_text(strip=True),
                        is_live=is_live,
                    )
                )
            return deps

        except Exception as e:
            self.logger.error("Departure Fetch Error: %s", e)
            return []

    def fetch_stop_info(self, stop_id: int) -> StopInfo | None:
        params = {"command": "planner", "action": "sd", "id": stop_id}
        try:
            r = self._get(params)
            soup = BeautifulSoup(r.text, "html.parser")

            name_tag = soup.find("input", {"id": "stop-name"})
            lat_tag = soup.find("input", {"id": "stop-lat"})
            lon_tag = soup.find("input", {"id": "stop-lon"})

            name = name_tag["value"] if name_tag else f"Stop {stop_id}"
            lat = float(lat_tag["value"]) if lat_tag else None
            lon = float(lon_tag["value"]) if lon_tag else None

            return StopInfo(stop_id=stop_id, name=name, lat=lat, lon=lon)

        except Exception as e:
            self.logger.error("Stop Info Error: %s", e)
            return None