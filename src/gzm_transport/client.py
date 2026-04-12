from __future__ import annotations

import requests
import logging
import time
import pandas as pd
from .static import StaticProvider
from .live import LiveProvider
from .models import VehiclePosition, Departure


class GZMTransport:

    SDIP_BASE_URL = "https://sdip.transportgzm.pl/main"

    def __init__(self, gtfs_path: str = ".", retries: int = 2):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "GZM-Analytics-Library/1.0",
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        self.static = StaticProvider(gtfs_path)
        self.live = LiveProvider(self.session, self.SDIP_BASE_URL, retries=retries)
        self.logger = logging.getLogger("GZM")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def download_gtfs(self, extract_to: str | None = None) -> str:
        return self.static.download_gtfs(extract_to)

    def get_all_vehicles(self) -> list[VehiclePosition]:
        return self.live.fetch_vehicle_positions()

    def get_departures(self, stop_id: int) -> list[Departure]:
        return self.live.fetch_stop_departures(stop_id)

    def vehicles_to_dataframe(self) -> pd.DataFrame:
        positions = self.live.fetch_vehicle_positions()
        if not positions:
            return pd.DataFrame()
        return pd.DataFrame([p.to_dict() for p in positions])

    def departures_to_dataframe(self, stop_id: int) -> pd.DataFrame:
        deps = self.live.fetch_stop_departures(stop_id)
        if not deps:
            return pd.DataFrame()
        return pd.DataFrame([d.to_dict() for d in deps])