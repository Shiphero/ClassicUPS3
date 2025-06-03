import pytest
from ClassicUPS3.ups import UPSConnection, UPSResult, TrackingInfo, Shipment


def test_upsconnection_init_with_all_params(ups_connection_params):
    """Test UPSConnection initialization with all parameters"""
    conn = UPSConnection(**ups_connection_params)
    assert conn.license_number == "TEST_LICENSE"
    assert conn.user_id == "TEST_USER"
    assert conn.password == "TEST_PASS"
    assert conn.shipper_number == "123456"
    assert conn.debug is True


def test_upsconnection_init_minimal_params():
    """Test UPSConnection initialization with minimal parameters"""
    conn = UPSConnection("LIC", "USER", "PASS")
    assert conn.license_number == "LIC"
    assert conn.user_id == "USER"
    assert conn.password == "PASS"
    assert conn.shipper_number is None
    assert conn.debug is False


def test_upsconnection_generate_xml_contains_credentials(ups_connection_params):
    """Test that _generate_xml includes access credentials"""
    conn = UPSConnection(**ups_connection_params)
    xml = conn._generate_xml("track", {"TrackingNumber": "1Z12345E6692804405"})
    
    assert "TEST_LICENSE" in xml
    assert "TEST_USER" in xml
    assert "TEST_PASS" in xml
    assert "TrackingNumber" in xml
    assert "1Z12345E6692804405" in xml
    assert "AccessRequest" in xml


def test_upsconnection_transmit_request_uses_test_urls_when_debug_true(mock_urlopen_factory, ups_connection_params):
    """Test that _transmit_request uses test URLs when debug=True"""
    ups_connection_params["debug"] = True
    conn = UPSConnection(**ups_connection_params)
    
    mock_urlopen_factory(fixture_file="track_response.xml")
    result = conn._transmit_request("track", {"TrackingNumber": "1Z12345E6692804405"})
    
    assert isinstance(result, UPSResult)
    assert b"TrackResponse" in result.response


def test_upsconnection_transmit_request_uses_production_urls_when_debug_false(mock_urlopen_factory, ups_connection_params):
    """Test that _transmit_request uses production URLs when debug=False"""
    ups_connection_params["debug"] = False
    conn = UPSConnection(**ups_connection_params)
    
    mock_urlopen_factory(fixture_file="track_response.xml")
    result = conn._transmit_request("track", {"TrackingNumber": "1Z12345E6692804405"})
    
    assert isinstance(result, UPSResult)
    assert b"TrackResponse" in result.response


def test_upsconnection_tracking_info_convenience_method(mock_urlopen_factory, ups_connection_params):
    """Test tracking_info convenience method returns TrackingInfo instance"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(fixture_file="track_response.xml")
    
    info = conn.tracking_info("1Z12345E6692804405")
    assert isinstance(info, TrackingInfo)
    assert info.tracking_number == "1Z12345E6692804405"


def test_upsconnection_create_shipment_convenience_method(mock_urlopen_factory, ups_connection_params, sample_addresses, sample_package):
    """Test create_shipment convenience method returns Shipment instance"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(response_mapping={
        b"ShipConfirm": "ship_confirm_response.xml",
        b"ShipAccept": "ship_accept_response.xml"
    })
    
    shipment = conn.create_shipment(
        sample_addresses["us_from"],
        sample_addresses["us_to"],
        sample_package["dimensions"],
        sample_package["weight"]
    )
    
    assert isinstance(shipment, Shipment)
    assert shipment.cost == 12.34
    assert shipment.tracking_number == "1Z9999999999999999"


def test_upsresult_xml_response_property():
    """Test xml_response property returns original response"""
    test_xml = b'<?xml version="1.0"?><TestResponse><Status>Success</Status></TestResponse>'
    result = UPSResult(test_xml)
    assert result.xml_response == test_xml


def test_upsresult_dict_response_property():
    """Test dict_response property converts XML to dictionary"""
    test_xml = b'<?xml version="1.0"?><TrackResponse><Shipment><Package><Activity><Status><StatusType><Code>I</Code></StatusType></Status><Date>20230520</Date></Activity></Package></Shipment></TrackResponse>'
    result = UPSResult(test_xml)
    
    dict_response = result.dict_response
    assert isinstance(dict_response, dict)
    assert "TrackResponse" in dict_response
    assert "Shipment" in dict_response["TrackResponse"]


def test_upsresult_dict_response_with_complex_structure(mock_urlopen_factory):
    """Test dict_response with a complex XML structure from fixture"""
    from pathlib import Path
    fixtures_dir = Path(__file__).parent / "fixtures"
    track_xml = (fixtures_dir / "track_response.xml").read_bytes()
    
    result = UPSResult(track_xml)
    dict_response = result.dict_response
    
    assert isinstance(dict_response, dict)
    assert "TrackResponse" in dict_response
    shipment = dict_response["TrackResponse"]["Shipment"]
    assert "Package" in shipment
    assert "Activity" in shipment["Package"]