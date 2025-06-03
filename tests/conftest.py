import io
import urllib.request
from pathlib import Path

import pytest


class MockResponse(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @property
    def status(self):
        return 200


@pytest.fixture
def mock_urlopen_factory(mocker):
    """Factory fixture to create URL open mocks based on fixture files or conditions"""

    def _mock_urlopen(response_mapping=None, fixture_file=None):
        """
        Create a mock urlopen that returns responses based on request content or a single fixture file.

        Args:
            response_mapping: Dict mapping request content checks to fixture filenames
                Example: {b"TrackRequest": "track_response.xml", b"ShipConfirm": "ship_confirm_response.xml"}
            fixture_file: Single fixture file to return for all requests
        """
        fixtures_dir = Path(__file__).parent / "fixtures"

        def mock_urlopen(url, data):
            if fixture_file:
                # Use single fixture file for all requests
                fixture_path = fixtures_dir / fixture_file
                response_data = fixture_path.read_bytes()
            elif response_mapping:
                # Use mapping to determine response
                response_data = None
                for check_bytes, filename in response_mapping.items():
                    if check_bytes in data:
                        fixture_path = fixtures_dir / filename
                        response_data = fixture_path.read_bytes()
                        break

                if response_data is None:
                    # Default fallback
                    response_data = b"<Unknown/>"
            else:
                response_data = b"<Unknown/>"

            return MockResponse(response_data)

        mocker.patch.object(urllib.request, "urlopen", side_effect=mock_urlopen)
        return mock_urlopen

    return _mock_urlopen


@pytest.fixture
def ups_connection_params():
    """Standard UPS connection parameters for testing"""
    return {
        "license_number": "TEST_LICENSE",
        "user_id": "TEST_USER",
        "password": "TEST_PASS",
        "shipper_number": "123456",
        "debug": True,
    }


@pytest.fixture
def sample_addresses():
    """Sample US and international addresses for testing"""
    return {
        "us_from": {
            "name": "US Sender",
            "attn": "Sender Attn",
            "phone": "555-1111",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "New York",
            "state": "NY",
            "country": "US",
            "postal_code": "10001",
        },
        "us_to": {
            "name": "US Recipient",
            "company": "Recipient Co",
            "phone": "555-2222",
            "address1": "456 Elm St",
            "address2": "Apt 2",
            "city": "Los Angeles",
            "state": "CA",
            "country": "US",
            "postal_code": "90210",
        },
        "intl_from": {
            "name": "International Sender",
            "attn": "Sender Attn",
            "phone": "555-1111",
            "address1": "123 International St",
            "city": "Toronto",
            "state": "ON",
            "country": "CA",
            "postal_code": "M5V 3A8",
        },
        "intl_to": {
            "name": "International Recipient",
            "phone": "555-2222",
            "address1": "456 Global Ave",
            "city": "London",
            "state": "EN",
            "country": "GB",
            "postal_code": "SW1A 1AA",
        },
    }


@pytest.fixture
def sample_package():
    """Sample package dimensions and weight for testing"""
    return {"dimensions": {"length": "10", "width": "5", "height": "3"}, "weight": "2"}
