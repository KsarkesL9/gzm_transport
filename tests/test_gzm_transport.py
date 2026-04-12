import zipfile
import io
import pytest
from unittest.mock import patch, MagicMock, call

from gzm_transport.models import VehiclePosition, Departure, StopInfo
from gzm_transport.client import GZMTransport
from gzm_transport.static import StaticProvider
from gzm_transport.live import LiveProvider


SAMPLE_VEHICLE_JSON = [
    {"l": "14", "v": "KA-1234", "d": "Katowice Plac Wolności", "lat": 182_520_000, "lon": 68_940_000},
    {"l": "T6", "v": "TR-5678", "d": "Chorzów Batory", "lat": 50.2700, "lon": 19.0200},
    {"l": "36", "v": "BUS-0001", "d": "Sosnowiec Centrum"},
]

SAMPLE_DEPARTURE_HTML = """
<html><body>
<input type="hidden" name="stop-name" value="Katowice Rynek"/>
<input type="hidden" name="stop-lat" value="50.2599"/>
<input type="hidden" name="stop-lon" value="19.0216"/>
<div class="departure status-1">
    <div class="line">14</div>
    <div class="destination" title="Katowice Plac Wolności">Plac Wolności</div>
    <div class="time">3 min</div>
</div>
<div class="departure status-0">
    <div class="line">36</div>
    <div class="destination" title="Sosnowiec Centrum">Sosnowiec</div>
    <div class="time">12:45</div>
</div>
<div class="departure status-1">
    <div class="line">T6</div>
    <div class="destination" title="Chorzów Batory">Chorzów</div>
    <div class="time">1 min</div>
</div>
</body></html>
"""

SAMPLE_STOPS_CSV = """stop_id,stop_name,stop_lat,stop_lon
1,Katowice Rynek,50.2599,19.0216
2,Chorzów Batory,50.2967,19.0000
3,Sosnowiec Centrum,50.2866,19.1278
4,Katowice Plac Wolności,50.2588,19.0228
"""

SAMPLE_ROUTES_CSV = """route_id,route_short_name,route_long_name,route_type
1,14,Linia 14,3
2,36,Linia 36,3
3,T6,Tramwaj T6,0
"""

SAMPLE_TRIPS_CSV = """trip_id,route_id,service_id,trip_headsign
T001,1,WD,Katowice Plac Wolności
T002,2,WD,Sosnowiec Centrum
"""

SAMPLE_STOP_TIMES_CSV = """trip_id,arrival_time,departure_time,stop_id,stop_sequence
T001,08:00:00,08:00:00,1,1
T001,08:10:00,08:10:00,4,2
T002,09:00:00,09:00:00,3,1
"""

SAMPLE_CALENDAR_CSV = """service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date
WD,1,1,1,1,1,0,0,20260101,20261231
"""


def _make_gtfs_zip(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content.strip())
    return buf.getvalue()


class TestVehiclePosition:
    def test_creation(self):
        vp = VehiclePosition(
            timestamp="2026-01-01T10:00:00",
            line_name="14",
            vehicle_id="KA-1234",
            direction="Centrum",
            lat=50.259,
            lon=19.021,
        )
        assert vp.line_name == "14"
        assert vp.lat == 50.259

    def test_to_dict(self):
        vp = VehiclePosition("t", "14", "v1", "d", 1.0, 2.0)
        d = vp.to_dict()
        assert isinstance(d, dict)
        assert d["line_name"] == "14"
        assert d["lat"] == 1.0


class TestDeparture:
    def test_creation(self):
        dep = Departure(
            timestamp="2026-01-01 10:00:00",
            stop_id=1,
            line_name="14",
            destination="Centrum",
            departure_time="3 min",
            is_live=True,
        )
        assert dep.is_live is True
        assert dep.stop_id == 1

    def test_to_dict(self):
        dep = Departure("t", 1, "14", "d", "5 min", False)
        d = dep.to_dict()
        assert isinstance(d, dict)
        assert d["is_live"] is False


class TestStopInfo:
    def test_creation_with_coords(self):
        si = StopInfo(stop_id=1, name="Rynek", lat=50.0, lon=19.0)
        assert si.name == "Rynek"

    def test_creation_without_coords(self):
        si = StopInfo(stop_id=2, name="Test")
        assert si.lat is None
        assert si.lon is None

    def test_to_dict(self):
        si = StopInfo(1, "Test", 50.0, 19.0)
        d = si.to_dict()
        assert d["stop_id"] == 1
        assert d["name"] == "Test"


class TestStaticProvider:

    @pytest.fixture()
    def gtfs_dir(self, tmp_path):
        files = {
            "stops.txt": SAMPLE_STOPS_CSV,
            "routes.txt": SAMPLE_ROUTES_CSV,
            "trips.txt": SAMPLE_TRIPS_CSV,
            "stop_times.txt": SAMPLE_STOP_TIMES_CSV,
            "calendar.txt": SAMPLE_CALENDAR_CSV,
        }
        for name, content in files.items():
            (tmp_path / name).write_text(content.strip(), encoding="utf-8")
        return tmp_path

    def test_get_stops(self, gtfs_dir):
        sp = StaticProvider(str(gtfs_dir))
        df = sp.get_stops()
        assert len(df) == 4
        assert "stop_name" in df.columns

    def test_get_routes(self, gtfs_dir):
        sp = StaticProvider(str(gtfs_dir))
        df = sp.get_routes()
        assert len(df) == 3
        assert "route_short_name" in df.columns

    def test_get_trips(self, gtfs_dir):
        sp = StaticProvider(str(gtfs_dir))
        df = sp.get_trips()
        assert len(df) == 2

    def test_get_stop_times(self, gtfs_dir):
        sp = StaticProvider(str(gtfs_dir))
        df = sp.get_stop_times()
        assert len(df) == 3

    def test_get_calendar(self, gtfs_dir):
        sp = StaticProvider(str(gtfs_dir))
        df = sp.get_calendar()
        assert len(df) == 1

    def test_get_active_lines(self, gtfs_dir):
        sp = StaticProvider(str(gtfs_dir))
        lines = sp.get_active_lines()
        assert len(lines) == 3
        short_names = [l[0] for l in lines]
        assert "14" in short_names

    def test_search_stops(self, gtfs_dir):
        sp = StaticProvider(str(gtfs_dir))
        result = sp.search_stops("katowice")
        assert len(result) == 2

    def test_search_stops_no_results(self, gtfs_dir):
        sp = StaticProvider(str(gtfs_dir))
        result = sp.search_stops("Warszawa")
        assert len(result) == 0

    def test_get_stop_schedule(self, gtfs_dir):
        sp = StaticProvider(str(gtfs_dir))
        sched = sp.get_stop_schedule("1")
        assert len(sched) == 1

    def test_available_files(self, gtfs_dir):
        sp = StaticProvider(str(gtfs_dir))
        files = sp.available_files()
        assert "stops.txt" in files
        assert "routes.txt" in files

    def test_missing_file_raises(self, gtfs_dir):
        sp = StaticProvider(str(gtfs_dir))
        with pytest.raises(FileNotFoundError):
            sp.get_shapes()

    def test_available_files_empty_dir(self, tmp_path):
        sp = StaticProvider(str(tmp_path))
        assert sp.available_files() == []

    def test_available_files_nonexistent_dir(self):
        sp = StaticProvider("/nonexistent/path")
        assert sp.available_files() == []

    @patch("gzm_transport.static.requests.get")
    def test_download_gtfs(self, mock_get, tmp_path):
        zip_bytes = _make_gtfs_zip({
            "stops.txt": SAMPLE_STOPS_CSV,
            "routes.txt": SAMPLE_ROUTES_CSV,
        })
        mock_resp = MagicMock()
        mock_resp.content = zip_bytes
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        dest = str(tmp_path / "gtfs_out")
        sp = StaticProvider(".")
        result = sp.download_gtfs(dest)

        assert result == dest
        assert sp.path == dest
        df = sp.get_stops()
        assert len(df) == 4

    @patch("gzm_transport.static.requests.get")
    def test_download_gtfs_http_error(self, mock_get):
        from requests.exceptions import HTTPError
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = HTTPError("404")
        mock_get.return_value = mock_resp

        sp = StaticProvider(".")
        with pytest.raises(HTTPError):
            sp.download_gtfs("/tmp/out")


class TestLiveProvider:

    @pytest.fixture()
    def provider(self):
        session = MagicMock()
        return LiveProvider(session, "https://sdip.transportgzm.pl/main", retries=0)

    def test_fetch_vehicle_positions(self, provider):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_VEHICLE_JSON
        mock_resp.raise_for_status = MagicMock()
        provider.session.get.return_value = mock_resp

        positions = provider.fetch_vehicle_positions()
        assert len(positions) == 3
        assert positions[0].line_name == "14"
        assert 50.0 < positions[0].lat < 51.0

    def test_fetch_vehicle_positions_normal_coords(self, provider):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_VEHICLE_JSON
        mock_resp.raise_for_status = MagicMock()
        provider.session.get.return_value = mock_resp

        positions = provider.fetch_vehicle_positions()
        assert positions[1].lat == pytest.approx(50.27, abs=0.01)
        assert positions[1].lon == pytest.approx(19.02, abs=0.01)

    def test_fetch_vehicle_positions_missing_coords(self, provider):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_VEHICLE_JSON
        mock_resp.raise_for_status = MagicMock()
        provider.session.get.return_value = mock_resp

        positions = provider.fetch_vehicle_positions()
        assert positions[2].lat == 0.0
        assert positions[2].lon == 0.0

    def test_fetch_vehicle_positions_empty(self, provider):
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_resp.raise_for_status = MagicMock()
        provider.session.get.return_value = mock_resp

        positions = provider.fetch_vehicle_positions()
        assert positions == []

    def test_fetch_vehicle_positions_error(self, provider):
        provider.session.get.side_effect = ConnectionError("timeout")
        positions = provider.fetch_vehicle_positions()
        assert positions == []

    def test_fetch_gps_stream_alias(self, provider):
        assert provider.fetch_gps_stream.__func__ is provider.fetch_vehicle_positions.__func__

    def test_fetch_stop_departures(self, provider):
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_DEPARTURE_HTML
        mock_resp.raise_for_status = MagicMock()
        provider.session.get.return_value = mock_resp

        deps = provider.fetch_stop_departures(10001)
        assert len(deps) == 3

    def test_departure_is_live_flag(self, provider):
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_DEPARTURE_HTML
        mock_resp.raise_for_status = MagicMock()
        provider.session.get.return_value = mock_resp

        deps = provider.fetch_stop_departures(10001)
        assert deps[0].is_live is True
        assert deps[1].is_live is False
        assert deps[2].is_live is True

    def test_departure_line_names(self, provider):
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_DEPARTURE_HTML
        mock_resp.raise_for_status = MagicMock()
        provider.session.get.return_value = mock_resp

        deps = provider.fetch_stop_departures(10001)
        assert deps[0].line_name == "14"
        assert deps[1].line_name == "36"
        assert deps[2].line_name == "T6"

    def test_departure_destination_from_title(self, provider):
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_DEPARTURE_HTML
        mock_resp.raise_for_status = MagicMock()
        provider.session.get.return_value = mock_resp

        deps = provider.fetch_stop_departures(10001)
        assert deps[0].destination == "Katowice Plac Wolności"
        assert deps[1].destination == "Sosnowiec Centrum"

    def test_fetch_departures_error(self, provider):
        provider.session.get.side_effect = ConnectionError("timeout")
        deps = provider.fetch_stop_departures(10001)
        assert deps == []

    def test_fetch_departures_empty_page(self, provider):
        mock_resp = MagicMock()
        mock_resp.text = "<html><body></body></html>"
        mock_resp.raise_for_status = MagicMock()
        provider.session.get.return_value = mock_resp

        deps = provider.fetch_stop_departures(999)
        assert deps == []

    def test_fetch_stop_info(self, provider):
        mock_resp = MagicMock()
        mock_resp.text = SAMPLE_DEPARTURE_HTML
        mock_resp.raise_for_status = MagicMock()
        provider.session.get.return_value = mock_resp

        info = provider.fetch_stop_info(10001)
        assert info is not None
        assert info.name == "Katowice Rynek"
        assert info.lat == pytest.approx(50.2599)
        assert info.lon == pytest.approx(19.0216)

    def test_fetch_stop_info_missing_inputs(self, provider):
        mock_resp = MagicMock()
        mock_resp.text = "<html><body></body></html>"
        mock_resp.raise_for_status = MagicMock()
        provider.session.get.return_value = mock_resp

        info = provider.fetch_stop_info(999)
        assert info is not None
        assert info.name == "Stop 999"
        assert info.lat is None

    def test_fetch_stop_info_error(self, provider):
        provider.session.get.side_effect = ConnectionError("timeout")
        info = provider.fetch_stop_info(10001)
        assert info is None


class TestLiveProviderRetry:

    @patch("time.sleep")
    def test_retry_succeeds_on_second_attempt(self, mock_sleep):
        session = MagicMock()
        provider = LiveProvider(session, "https://sdip.transportgzm.pl/main", retries=2)

        fail_resp = MagicMock()
        fail_resp.raise_for_status.side_effect = ConnectionError("fail")

        ok_resp = MagicMock()
        ok_resp.json.return_value = []
        ok_resp.raise_for_status = MagicMock()

        session.get.side_effect = [ConnectionError("fail"), ok_resp]

        positions = provider.fetch_vehicle_positions()
        assert positions == []
        assert session.get.call_count == 2

    @patch("time.sleep")
    def test_retry_exhausted(self, mock_sleep):
        session = MagicMock()
        provider = LiveProvider(session, "https://sdip.transportgzm.pl/main", retries=1)

        session.get.side_effect = ConnectionError("fail")

        positions = provider.fetch_vehicle_positions()
        assert positions == []
        assert session.get.call_count == 2

    def test_no_retry_when_zero(self):
        session = MagicMock()
        provider = LiveProvider(session, "https://sdip.transportgzm.pl/main", retries=0)

        session.get.side_effect = ConnectionError("fail")

        positions = provider.fetch_vehicle_positions()
        assert positions == []
        assert session.get.call_count == 1


class TestGZMTransport:

    def test_context_manager(self):
        with GZMTransport() as gzm:
            assert gzm.session is not None
            assert gzm.live is not None
            assert gzm.static is not None

    def test_has_static_and_live_providers(self):
        gzm = GZMTransport()
        assert isinstance(gzm.static, StaticProvider)
        assert isinstance(gzm.live, LiveProvider)

    def test_no_logging_basicconfig(self):
        import logging
        with patch.object(logging, "basicConfig") as mock_bc:
            GZMTransport()
            mock_bc.assert_not_called()

    def test_vehicles_to_dataframe_empty(self):
        with GZMTransport() as gzm:
            with patch.object(gzm.live, "fetch_vehicle_positions", return_value=[]):
                df = gzm.vehicles_to_dataframe()
                assert len(df) == 0

    def test_vehicles_to_dataframe(self):
        positions = [
            VehiclePosition("t", "14", "v1", "d", 50.0, 19.0),
            VehiclePosition("t", "36", "v2", "d", 50.1, 19.1),
        ]
        with GZMTransport() as gzm:
            with patch.object(gzm.live, "fetch_vehicle_positions", return_value=positions):
                df = gzm.vehicles_to_dataframe()
                assert len(df) == 2
                assert "line_name" in df.columns

    def test_departures_to_dataframe(self):
        departures = [
            Departure("t", 1, "14", "Centrum", "3 min", True),
        ]
        with GZMTransport() as gzm:
            with patch.object(gzm.live, "fetch_stop_departures", return_value=departures):
                df = gzm.departures_to_dataframe(1)
                assert len(df) == 1
                assert df.iloc[0]["is_live"] == True

    def test_custom_retries(self):
        gzm = GZMTransport(retries=5)
        assert gzm.live.retries == 5


class TestPackageImports:
    def test_import_main_class(self):
        from gzm_transport import GZMTransport
        assert GZMTransport is not None

    def test_import_models(self):
        from gzm_transport import VehiclePosition, Departure, StopInfo
        assert VehiclePosition is not None
        assert Departure is not None
        assert StopInfo is not None

    def test_import_providers(self):
        from gzm_transport import StaticProvider, LiveProvider
        assert StaticProvider is not None
        assert LiveProvider is not None

    def test_version(self):
        import gzm_transport
        assert gzm_transport.__version__ == "1.0.0"
