from pathlib import Path

from src.scraper import MISSING_INTERMEDIATE, _ca_bundle_path


def test_missing_intermediate_is_a_valid_pem_certificate():
    content = MISSING_INTERMEDIATE.read_text()
    assert content.startswith("-----BEGIN CERTIFICATE-----")
    assert content.strip().endswith("-----END CERTIFICATE-----")


def test_ca_bundle_includes_certifi_and_the_missing_intermediate():
    bundle_path = Path(_ca_bundle_path())
    bundle_content = bundle_path.read_bytes()

    assert MISSING_INTERMEDIATE.read_bytes() in bundle_content
    assert b"BEGIN CERTIFICATE" in bundle_content
