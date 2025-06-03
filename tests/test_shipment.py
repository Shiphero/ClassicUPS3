import pytest
import io
from ClassicUPS3.ups import UPSConnection, Shipment


def test_shipment_basic_success(mock_urlopen_factory, ups_connection_params, sample_addresses, sample_package):
    """Test basic successful shipment creation"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(response_mapping={
        b"ShipConfirm": "ship_confirm_response.xml",
        b"ShipAccept": "ship_accept_response.xml"
    })
    
    shipment = Shipment(
        conn,
        sample_addresses["us_from"],
        sample_addresses["us_to"],
        sample_package["dimensions"],
        sample_package["weight"]
    )
    
    assert shipment.cost == 12.34
    assert shipment.tracking_number == "1Z9999999999999999"


def test_shipment_with_reference_numbers_domestic(mock_urlopen_factory, ups_connection_params, sample_addresses, sample_package):
    """Test domestic shipment with reference numbers"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(response_mapping={
        b"ShipConfirm": "ship_confirm_response.xml",
        b"ShipAccept": "ship_accept_response.xml"
    })
    
    reference_numbers = ["REF1", ("CODE2", "REF2")]
    
    shipment = Shipment(
        conn,
        sample_addresses["us_from"],
        sample_addresses["us_to"],
        sample_package["dimensions"],
        sample_package["weight"],
        reference_numbers=reference_numbers
    )
    
    assert shipment.cost == 12.34
    assert shipment.tracking_number == "1Z9999999999999999"


def test_shipment_international_with_reference_numbers(mock_urlopen_factory, ups_connection_params, sample_addresses, sample_package):
    """Test international shipment with reference numbers and description"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(response_mapping={
        b"ShipConfirm": "ship_confirm_response.xml",
        b"ShipAccept": "ship_accept_response.xml"
    })
    
    reference_numbers = ["INTL-REF1", "INTL-REF2"]
    description = "International shipment description"
    
    shipment = Shipment(
        conn,
        sample_addresses["intl_from"],
        sample_addresses["intl_to"],
        sample_package["dimensions"],
        sample_package["weight"],
        reference_numbers=reference_numbers,
        description=description
    )
    
    assert shipment.cost == 12.34
    assert shipment.tracking_number == "1Z9999999999999999"


def test_shipment_with_delivery_confirmation(mock_urlopen_factory, ups_connection_params, sample_addresses, sample_package):
    """Test shipment with delivery confirmation"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(response_mapping={
        b"ShipConfirm": "ship_confirm_response.xml",
        b"ShipAccept": "ship_accept_response.xml"
    })
    
    shipment = Shipment(
        conn,
        sample_addresses["us_from"],
        sample_addresses["us_to"],
        sample_package["dimensions"],
        sample_package["weight"],
        delivery_confirmation="signature_required"
    )
    
    assert shipment.cost == 12.34
    assert shipment.tracking_number == "1Z9999999999999999"


def test_shipment_with_all_delivery_confirmation_types(mock_urlopen_factory, ups_connection_params, sample_addresses, sample_package):
    """Test shipment with different delivery confirmation types"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(response_mapping={
        b"ShipConfirm": "ship_confirm_response.xml",
        b"ShipAccept": "ship_accept_response.xml"
    })
    
    confirmation_types = [
        "no_signature",
        "signature_required", 
        "adult_signature_required",
        "usps_delivery_confiratmion"
    ]
    
    for confirmation_type in confirmation_types:
        shipment = Shipment(
            conn,
            sample_addresses["us_from"],
            sample_addresses["us_to"],
            sample_package["dimensions"],
            sample_package["weight"],
            delivery_confirmation=confirmation_type
        )
        assert shipment.cost == 12.34


def test_shipment_with_address2_fields(mock_urlopen_factory, ups_connection_params, sample_addresses, sample_package):
    """Test shipment with address2 fields populated"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(response_mapping={
        b"ShipConfirm": "ship_confirm_response.xml",
        b"ShipAccept": "ship_accept_response.xml"
    })
    
    # Use addresses that have address2 fields
    shipment = Shipment(
        conn,
        sample_addresses["us_from"],  # Has address2
        sample_addresses["us_to"],    # Has address2 and company
        sample_package["dimensions"],
        sample_package["weight"]
    )
    
    assert shipment.cost == 12.34
    assert shipment.tracking_number == "1Z9999999999999999"


def test_shipment_different_file_formats(mock_urlopen_factory, ups_connection_params, sample_addresses, sample_package):
    """Test shipment with different file formats"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(response_mapping={
        b"ShipConfirm": "ship_confirm_response.xml",
        b"ShipAccept": "ship_accept_response.xml"
    })
    
    file_formats = ["EPL", "GIF"]
    
    for file_format in file_formats:
        shipment = Shipment(
            conn,
            sample_addresses["us_from"],
            sample_addresses["us_to"],
            sample_package["dimensions"],
            sample_package["weight"],
            file_format=file_format
        )
        assert shipment.cost == 12.34


def test_shipment_different_shipping_services(mock_urlopen_factory, ups_connection_params, sample_addresses, sample_package):
    """Test shipment with different shipping services"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(response_mapping={
        b"ShipConfirm": "ship_confirm_response.xml",
        b"ShipAccept": "ship_accept_response.xml"
    })
    
    services = ["ground", "1dayair", "2dayair", "express"]
    
    for service in services:
        shipment = Shipment(
            conn,
            sample_addresses["us_from"],
            sample_addresses["us_to"],
            sample_package["dimensions"],
            sample_package["weight"],
            shipping_service=service
        )
        assert shipment.cost == 12.34


def test_shipment_different_units(mock_urlopen_factory, ups_connection_params, sample_addresses, sample_package):
    """Test shipment with different dimension and weight units"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(response_mapping={
        b"ShipConfirm": "ship_confirm_response.xml",
        b"ShipAccept": "ship_accept_response.xml"
    })
    
    shipment = Shipment(
        conn,
        sample_addresses["us_from"],
        sample_addresses["us_to"],
        sample_package["dimensions"],
        sample_package["weight"],
        dimensions_unit="CM",
        weight_unit="KGS"
    )
    
    assert shipment.cost == 12.34
    assert shipment.tracking_number == "1Z9999999999999999"


def test_shipment_get_label(mock_urlopen_factory, ups_connection_params, sample_addresses, sample_package):
    """Test get_label method returns base64 decoded bytes"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(response_mapping={
        b"ShipConfirm": "ship_confirm_response.xml",
        b"ShipAccept": "ship_accept_response.xml"
    })
    
    shipment = Shipment(
        conn,
        sample_addresses["us_from"],
        sample_addresses["us_to"],
        sample_package["dimensions"],
        sample_package["weight"]
    )
    
    label = shipment.get_label()
    assert isinstance(label, bytes)
    assert label == b'SomeBase64Image'  # From fixture


def test_shipment_save_label(mock_urlopen_factory, ups_connection_params, sample_addresses, sample_package):
    """Test save_label method writes to file descriptor"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(response_mapping={
        b"ShipConfirm": "ship_confirm_response.xml",
        b"ShipAccept": "ship_accept_response.xml"
    })
    
    shipment = Shipment(
        conn,
        sample_addresses["us_from"],
        sample_addresses["us_to"],
        sample_package["dimensions"],
        sample_package["weight"]
    )
    
    # Test saving to BytesIO
    buffer = io.BytesIO()
    shipment.save_label(buffer)
    buffer.seek(0)
    saved_data = buffer.read()
    
    assert saved_data == b'SomeBase64Image'


def test_shipment_error_handling(mock_urlopen_factory, ups_connection_params, sample_addresses, sample_package):
    """Test shipment error handling when API returns error"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(response_mapping={
        b"ShipConfirm": "ship_error_response.xml"
    })
    
    with pytest.raises(Exception) as exc_info:
        Shipment(
            conn,
            sample_addresses["us_from"],
            sample_addresses["us_to"],
            sample_package["dimensions"],
            sample_package["weight"]
        )
    
    assert "The XML document is well formed but the document is not valid" in str(exc_info.value)


def test_shipment_cost_property(mock_urlopen_factory, ups_connection_params, sample_addresses, sample_package):
    """Test cost property returns float value"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(response_mapping={
        b"ShipConfirm": "ship_confirm_response.xml",
        b"ShipAccept": "ship_accept_response.xml"
    })
    
    shipment = Shipment(
        conn,
        sample_addresses["us_from"],
        sample_addresses["us_to"],
        sample_package["dimensions"],
        sample_package["weight"]
    )
    
    cost = shipment.cost
    assert isinstance(cost, float)
    assert cost == 12.34


def test_shipment_tracking_number_property(mock_urlopen_factory, ups_connection_params, sample_addresses, sample_package):
    """Test tracking_number property returns string"""
    conn = UPSConnection(**ups_connection_params)
    mock_urlopen_factory(response_mapping={
        b"ShipConfirm": "ship_confirm_response.xml",
        b"ShipAccept": "ship_accept_response.xml"
    })
    
    shipment = Shipment(
        conn,
        sample_addresses["us_from"],
        sample_addresses["us_to"],
        sample_package["dimensions"],
        sample_package["weight"]
    )
    
    tracking_number = shipment.tracking_number
    assert isinstance(tracking_number, str)
    assert tracking_number == "1Z9999999999999999"


def test_shipment_shipping_services_constants():
    """Test that all shipping service constants are defined correctly"""
    expected_services = {
        "1dayair": "01",
        "2dayair": "02", 
        "ground": "03",
        "express": "07",
        "worldwide_expedited": "08",
        "standard": "11",
        "3_day_select": "12",
        "next_day_air_saver": "13",
        "next_day_air_early_am": "14",
        "express_plus": "54",
        "2nd_day_air_am": "59",
        "ups_saver": "65",
        "ups_today_standard": "82",
        "ups_today_dedicated_courier": "83",
        "ups_today_intercity": "84",
        "ups_today_express": "85",
        "ups_today_express_saver": "86"
    }
    
    for service_name, service_code in expected_services.items():
        assert Shipment.SHIPPING_SERVICES[service_name] == service_code


def test_shipment_dcis_types_constants():
    """Test that all DCIS types constants are defined correctly"""
    expected_dcis_types = {
        "no_signature": 1,
        "signature_required": 2,
        "adult_signature_required": 3,
        "usps_delivery_confiratmion": 4
    }
    
    for dcis_name, dcis_code in expected_dcis_types.items():
        assert Shipment.DCIS_TYPES[dcis_name] == dcis_code