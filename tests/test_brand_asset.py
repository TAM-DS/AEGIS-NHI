"""Ensure checked-in Beast brand asset can be rendered without external hosting."""

import struct
from pathlib import Path


def test_brand_mascot_png_is_available_and_transparent_capable():
    root = Path(__file__).resolve().parents[1]
    asset = root / "docs/images/aegis-beast-guardian.png"
    data = asset.read_bytes()
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(data) > 1200
    width, height = struct.unpack(">II", data[16:24])
    assert (width, height) == (96, 96)
    assert b"PLTE" in data
    assert b"tRNS" in data
