import io
import types
import pytest
import urllib.request
from ClassicUPS3.ups import UPSConnection, UPSResult, TrackingInfo, Shipment

class DummyResponse(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    @property
    def status(self): return 200

@pytest.fixture
def dummy_xml_response():
    # Minimal valid XML for UPSResult and TrackingInfo
    return b"""<?xml version="1.0"?>
    <TrackResponse>
      <Shipment>
        <Package>
          <Activity>
            <Status>
              <StatusType>
                <Code>I</Code>
              </StatusType>
            </Status>
            <Date>20230520</Date>
          </Activity>
          <Activity>
            <Status>
              <StatusType>
                <Code>D</Code>
              </StatusType>
            </Status>
            <Date>20230522</Date>
          </Activity>
        </Package>
      </Shipment>
    </TrackResponse>"""

@pytest.fixture
def dummy_shipment_confirm_response():
    # Minimal valid XML for Shipment confirm
    return b"""<?xml version="1.0"?>
    <ShipmentConfirmResponse>
      <ShipmentDigest>digest123</ShipmentDigest>
      <ShipmentCharges>
        <TotalCharges>
          <MonetaryValue>12.34</MonetaryValue>
        </TotalCharges>
      </ShipmentCharges>
      <ShipmentIdentificationNumber>1Z9999999999999999</ShipmentIdentificationNumber>
      <Response>
        <ResponseStatusCode>1</ResponseStatusCode>
      </Response>
    </ShipmentConfirmResponse>"""

@pytest.fixture
def dummy_shipment_accept_response():
    # Minimal valid XML for Shipment accept
    return b"""<?xml version="1.0"?>
    <ShipmentAcceptResponse>
      <ShipmentResults>
        <PackageResults>
          <LabelImage>
            <GraphicImage>U29tZUJhc2U2NEltYWdl</GraphicImage>
          </LabelImage>
        </PackageResults>
      </ShipmentResults>
    </ShipmentAcceptResponse>"""

@pytest.fixture
def monkeypatched_urlopen(monkeypatch, dummy_xml_response, dummy_shipment_confirm_response, dummy_shipment_accept_response):
    """
    Patch urllib.request.urlopen to return different responses depending on the request XML.
    """
    def fake_urlopen(url, data):
        print("Request data:", data)
        if b"TrackingNumber" in data:
            return DummyResponse(dummy_xml_response)
        elif b"ShipConfirm" in data:
            return DummyResponse(dummy_shipment_confirm_response)
        elif b"ShipAccept" in data:
            return DummyResponse(dummy_shipment_accept_response)
        else:
            return DummyResponse(b"<Unknown/>")
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

def test_upsconnection_init_and_attrs():
    conn = UPSConnection("LIC", "USER", "PASS", shipper_number="123", debug=True)
    assert conn.license_number == "LIC"
    assert conn.user_id == "USER"
    assert conn.password == "PASS"
    assert conn.shipper_number == "123"
    assert conn.debug is True

def test_generate_xml_contains_credentials():
    conn = UPSConnection("LIC", "USER", "PASS")
    xml = conn._generate_xml("track", {"foo": "bar"})
    assert "LIC" in xml
    assert "USER" in xml
    assert "PASS" in xml
    assert "foo" in xml

def test_transmit_request_selects_test_url(monkeypatched_urlopen):
    conn = UPSConnection("LIC", "USER", "PASS", debug=True)
    # Should use test_urls
    result = conn._transmit_request("track", {"TrackingNumber": "1Z12345E6692804405"})
    assert isinstance(result, UPSResult)
    assert b"TrackResponse" in result.response

def test_transmit_request_selects_production_url(monkeypatched_urlopen):
    conn = UPSConnection("LIC", "USER", "PASS", debug=False)
    # Should use production_urls
    result = conn._transmit_request("track", {"TrackingNumber": "1Z12345E6692804405"})
    assert isinstance(result, UPSResult)
    assert b"TrackResponse" in result.response

def test_tracking_info_properties(monkeypatched_urlopen):
    conn = UPSConnection("LIC", "USER", "PASS", debug=True)
    info = TrackingInfo(conn, "1Z12345E6692804405")
    acts = info.shipment_activities
    assert isinstance(acts, list)
    assert acts[0]["Status"]["StatusType"]["Code"] == "I"
    assert info.in_transit is True
    assert info.delivered.year == 2023
    assert info.delivered.month == 5
    assert info.delivered.day == 22

def test_upsresult_properties(dummy_xml_response):
    result = UPSResult(dummy_xml_response)
    assert result.xml_response == dummy_xml_response
    d = result.dict_response
    assert "TrackResponse" in d

def test_tracking_info_single_activity(monkeypatch, dummy_xml_response):
    # Patch dummy_xml_response to only have one Activity (not a list)
    single_activity_xml = b"""<?xml version="1.0"?>
    <TrackResponse>
      <Shipment>
        <Package>
          <Activity>
            <Status>
              <StatusType>
                <Code>I</Code>
              </StatusType>
            </Status>
            <Date>20230520</Date>
          </Activity>
        </Package>
      </Shipment>
    </TrackResponse>"""
    def fake_urlopen(url, data):
        return DummyResponse(single_activity_xml)
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    conn = UPSConnection("LIC", "USER", "PASS", debug=True)
    info = TrackingInfo(conn, "1Z12345E6692804405")
    acts = info.shipment_activities
    assert isinstance(acts, list)
    assert len(acts) == 1

def test_shipment_success(monkeypatched_urlopen):
    conn = UPSConnection("LIC", "USER", "PASS", shipper_number="123", debug=True)
    from_addr = {
        "name": "Sender",
        "attn": "Sender Attn",
        "phone": "555-1111",
        "address1": "123 Main St",
        "city": "City",
        "state": "ST",
        "country": "US",
        "postal_code": "12345"
    }
    to_addr = {
        "name": "Recipient",
        "phone": "555-2222",
        "address1": "456 Elm St",
        "city": "Town",
        "state": "TS",
        "country": "US",
        "postal_code": "67890"
    }
    dimensions = {"length": "10", "width": "5", "height": "3"}
    weight = "2"
    shipment = Shipment(conn, from_addr, to_addr, dimensions, weight)
    assert shipment.cost == 12.34
    assert shipment.tracking_number == "1Z9999999999999999"
    label = shipment.get_label()
    assert isinstance(label, bytes)
    assert label == b'SomeBase64Image'
    # Test save_label
    buf = io.BytesIO()
    shipment.save_label(buf)
    buf.seek(0)
    assert buf.read() == b'SomeBase64Image'

def test_shipment_with_reference_and_address2(monkeypatched_urlopen):
    conn = UPSConnection("LIC", "USER", "PASS", shipper_number="123", debug=True)
    from_addr = {
        "name": "Sender",
        "attn": "Sender Attn",
        "phone": "555-1111",
        "address1": "123 Main St",
        "address2": "Suite 100",
        "city": "City",
        "state": "ST",
        "country": "US",
        "postal_code": "12345"
    }
    to_addr = {
        "name": "Recipient",
        "company": "Recipient Co",
        "phone": "555-2222",
        "address1": "456 Elm St",
        "address2": "Apt 2",
        "city": "Town",
        "state": "TS",
        "country": "US",
        "postal_code": "67890"
    }
    dimensions = {"length": "10", "width": "5", "height": "3"}
    weight = "2"
    reference_numbers = ["REF1", ("CODE2", "REF2")]
    shipment = Shipment(conn, from_addr, to_addr, dimensions, weight, reference_numbers=reference_numbers)
    assert shipment.cost == 12.34

def test_shipment_error(monkeypatch, dummy_shipment_confirm_response):
    # Patch urlopen to return a ShipmentConfirmResponse without ShipmentDigest
    error_xml = b"""<?xml version="1.0"?>
    <ShipmentConfirmResponse>
      <Response>
        <Error>
          <ErrorDescription>Some error occurred</ErrorDescription>
        </Error>
      </Response>
    </ShipmentConfirmResponse>"""
    def fake_urlopen(url, data):
        if b"ShipConfirm" in data:
            return DummyResponse(error_xml)
        else:
            return DummyResponse(b"<Unknown/>")
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    conn = UPSConnection("LIC", "USER", "PASS", shipper_number="123", debug=True)
    from_addr = {
        "name": "Sender",
        "attn": "Sender Attn",
        "phone": "555-1111",
        "address1": "123 Main St",
        "city": "City",
        "state": "ST",
        "country": "US",
        "postal_code": "12345"
    }
    to_addr = {
        "name": "Recipient",
        "phone": "555-2222",
        "address1": "456 Elm St",
        "city": "Town",
        "state": "TS",
        "country": "US",
        "postal_code": "67890"
    }
    dimensions = {"length": "10", "width": "5", "height": "3"}
    weight = "2"
    with pytest.raises(Exception) as excinfo:
        Shipment(conn, from_addr, to_addr, dimensions, weight)
    assert "Some error occurred" in str(excinfo.value)
