from datetime import datetime

from ClassicUPS3.ups import TrackingInfo, UPSConnection


def test_tracking_info_initialization(mock_urlopen_factory, ups_connection_params):
    """Test TrackingInfo initialization and basic properties"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(fixture_file="track_response.xml")

    info = TrackingInfo(conn, "1Z12345E6692804405")
    assert info.tracking_number == "1Z12345E6692804405"
    assert info.result is not None


def test_shipment_activities_parsed_as_list(mock_urlopen_factory, ups_connection_params):
    """Test that shipment_activities returns a list of activities"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(fixture_file="track_response.xml")

    info = TrackingInfo(conn, "1Z12345E6692804405")
    activities = info.shipment_activities

    assert isinstance(activities, list)
    assert len(activities) == 2

    first_activity = activities[0]
    assert first_activity["Status"]["StatusType"]["Code"] == "I"
    assert first_activity["Date"] == "20230520"


def test_shipment_activities_single_activity_becomes_list(mock_urlopen_factory, ups_connection_params):
    """Test that single activity is converted to list format"""
    conn = UPSConnection(**ups_connection_params)

    # Create a custom mock that returns single activity (not in list format)
    single_activity_mapping = {b"TrackingNumber": "track_response_single_activity.xml"}
    mock_urlopen_factory(response_mapping=single_activity_mapping)

    info = TrackingInfo(conn, "1Z12345E6692804405")
    activities = info.shipment_activities

    assert isinstance(activities, list)
    assert len(activities) == 1
    assert activities[0]["Status"]["StatusType"]["Code"] == "I"


def test_in_transit_property_true(mock_urlopen_factory, ups_connection_params):
    """Test in_transit property returns True when package has 'I' status"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(fixture_file="track_response.xml")

    info = TrackingInfo(conn, "1Z12345E6692804405")
    assert info.in_transit is True


def test_in_transit_property_false(mock_urlopen_factory, ups_connection_params):
    """Test in_transit property returns False when package has no 'I' status"""
    conn = UPSConnection(**ups_connection_params)
    # Use fixture with only delivered status (no 'I' status activities)
    mock_urlopen_factory(fixture_file="track_response_delivered_only.xml")

    info = TrackingInfo(conn, "1Z12345E6692804405")
    assert info.in_transit is False


def test_delivered_property_returns_datetime(mock_urlopen_factory, ups_connection_params):
    """Test delivered property returns datetime object for delivered packages"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(fixture_file="track_response.xml")

    info = TrackingInfo(conn, "1Z12345E6692804405")
    delivered_date = info.delivered

    assert isinstance(delivered_date, datetime)
    assert delivered_date == datetime.strptime("20230522", "%Y%m%d")
    assert delivered_date.year == 2023
    assert delivered_date.month == 5
    assert delivered_date.day == 22


def test_delivered_property_returns_none_when_not_delivered(mock_urlopen_factory, ups_connection_params):
    """Test delivered property returns None when package is not delivered"""
    conn = UPSConnection(**ups_connection_params)
    # Use fixture with only in-transit status (no 'D' status activities)
    mock_urlopen_factory(fixture_file="track_response_in_transit_only.xml")

    info = TrackingInfo(conn, "1Z12345E6692804405")
    delivered_date = info.delivered
    assert delivered_date is None


def test_tracking_info_with_various_status_codes(mock_urlopen_factory, ups_connection_params):
    """Test TrackingInfo handles various UPS status codes correctly"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(fixture_file="track_response.xml")

    info = TrackingInfo(conn, "1Z12345E6692804405")
    activities = info.shipment_activities

    # Verify we can handle different status types
    status_codes = [activity["Status"]["StatusType"]["Code"] for activity in activities]
    assert "I" in status_codes  # In Transit
    assert "D" in status_codes  # Delivered

    # Test that the activities are properly structured
    for activity in activities:
        assert "Status" in activity
        assert "StatusType" in activity["Status"]
        assert "Code" in activity["Status"]["StatusType"]
        assert "Date" in activity


def test_tracking_info_transmit_request_called_correctly(mock_urlopen_factory, ups_connection_params, mocker):
    """Test that TrackingInfo calls _transmit_request with correct parameters"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(fixture_file="track_response.xml")

    # Spy on the _transmit_request method
    spy = mocker.spy(conn, "_transmit_request")

    TrackingInfo(conn, "1Z12345E6692804405")

    # Verify _transmit_request was called with correct parameters
    spy.assert_called_once_with(
        "track",
        {
            "TrackRequest": {
                "Request": {
                    "TransactionReference": {
                        "CustomerContext": "Get tracking status",
                        "XpciVersion": "1.0",
                    },
                    "RequestAction": "Track",
                    "RequestOption": "activity",
                },
                "TrackingNumber": "1Z12345E6692804405",
            },
        },
    )
