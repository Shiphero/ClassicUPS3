import io
import urllib.request
from datetime import datetime
from pathlib import Path

import pytest
from ClassicUPS3 import UPSConnection, TrackingInfo


@pytest.fixture
def mock_urlopen_factory(monkeypatch):
    def _mock(file_name: str):
        path = Path(__file__).parent / "fixtures" / file_name
        data = path.read_bytes()

        class FakeResponse(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): self.close()
            @property
            def status(self): return 200

        monkeypatch.setattr(
            urllib.request, "urlopen", lambda *a, **kw: FakeResponse(data)
        )

    return _mock

@pytest.fixture
def mock_track_response(mock_urlopen_factory):
    return mock_urlopen_factory("track_response.xml")


def test_shipment_activities_parsed_as_list(mock_track_response):
    conn = UPSConnection("LIC", "USER", "PASS", shipper_number="123", debug=True)
    info = TrackingInfo(conn, "1Z12345E6692804405")

    activities = info.shipment_activities
    assert isinstance(activities, list)
    assert len(activities) == 2

    first = activities[0]
    assert first["Status"]["StatusType"]["Code"] == "I"
    assert first["Date"] == "20230520"


def test_in_transit_and_delivered_properties(mock_track_response):
    conn = UPSConnection("LIC", "USER", "PASS", shipper_number="123", debug=True)
    info = TrackingInfo(conn, "1Z12345E6692804405")

    assert info.in_transit is True

    delivered_date = info.delivered
    assert isinstance(delivered_date, datetime)
    assert delivered_date == datetime.strptime("20230522", "%Y%m%d")
