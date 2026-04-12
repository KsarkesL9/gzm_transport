from __future__ import annotations

import pandas as pd
import os
import zipfile
import logging
import requests
from io import BytesIO


class StaticProvider:

    GTFS_FILES = [
        "agency.txt", "calendar.txt", "calendar_dates.txt",
        "routes.txt", "shapes.txt", "stop_times.txt",
        "stops.txt", "trips.txt", "feed_info.txt",
    ]

    GTFS_URL = (
        "https://otwartedane.metropoliagzm.pl/dataset/"
        "9285399c-01da-4a96-abf3-59f8c2d7e8d7/resource/"
        "8cfa8e6c-e151-409e-b643-1f9047f01541/download"
    )

    def __init__(self, data_path: str):
        self.path = data_path
        self.logger = logging.getLogger(__name__)

    def download_gtfs(self, extract_to: str | None = None) -> str:
        dest = extract_to or self.path
        os.makedirs(dest, exist_ok=True)

        self.logger.info("Pobieranie GTFS z %s", self.GTFS_URL)
        r = requests.get(self.GTFS_URL, timeout=60)
        r.raise_for_status()

        with zipfile.ZipFile(BytesIO(r.content)) as zf:
            zf.extractall(dest)

        self.path = dest
        return dest

    def _read(self, filename: str) -> pd.DataFrame:
        filepath = os.path.join(self.path, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(
                f"Brak pliku {filename} w {self.path}. "
                "Użyj download_gtfs() aby pobrać dane."
            )
        return pd.read_csv(filepath, dtype=str)

    def get_stops(self) -> pd.DataFrame:
        return self._read("stops.txt")

    def get_routes(self) -> pd.DataFrame:
        return self._read("routes.txt")

    def get_trips(self) -> pd.DataFrame:
        return self._read("trips.txt")

    def get_stop_times(self) -> pd.DataFrame:
        return self._read("stop_times.txt")

    def get_calendar(self) -> pd.DataFrame:
        return self._read("calendar.txt")

    def get_calendar_dates(self) -> pd.DataFrame:
        return self._read("calendar_dates.txt")

    def get_shapes(self) -> pd.DataFrame:
        return self._read("shapes.txt")

    def get_agency(self) -> pd.DataFrame:
        return self._read("agency.txt")

    def get_active_lines(self) -> list:
        routes = self.get_routes()
        return (
            routes[["route_short_name", "route_long_name"]]
            .drop_duplicates()
            .values.tolist()
        )

    def search_stops(self, query: str) -> pd.DataFrame:
        stops = self.get_stops()
        mask = stops["stop_name"].str.contains(query, case=False, na=False)
        return stops[mask]

    def get_stop_schedule(self, stop_id: str) -> pd.DataFrame:
        st = self.get_stop_times()
        return st[st["stop_id"] == str(stop_id)]

    def available_files(self) -> list[str]:
        if not os.path.isdir(self.path):
            return []
        return [
            f for f in os.listdir(self.path)
            if f.endswith(".txt") and f in self.GTFS_FILES
        ]