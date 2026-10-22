import pytest
from app.core import config

def test_validate_jwt_config_succeeds_when_all_settings_are_present(monkeypatch):
    monkeypatch.setattr(config, "JWT_PUBLIC_KEY", "test-public-key")
    monkeypatch.setattr(config, "JWT_ISSUER", "nowarie-test")
    monkeypatch.setattr(config, "JWT_AUDIENCE", "nowarie-realtime")

    config.validate_jwt_config()

def test_validate_jwt_config_fails_when_issuer_is_missing(monkeypatch):
    monkeypatch.setattr(config, "JWT_PUBLIC_KEY", "test-public-key")
    monkeypatch.setattr(config, "JWT_ISSUER", None)
    monkeypatch.setattr(config, "JWT_AUDIENCE", "nowarie-realtime")

    with pytest.raises(ValueError, match="JWT_ISSUER"):
        config.validate_jwt_config()

def test_validate_jwt_config_fails_when_multiple_settings_are_missing(monkeypatch):
    monkeypatch.setattr(config, "JWT_PUBLIC_KEY", "test-public-key")
    monkeypatch.setattr(config, "JWT_ISSUER", None)
    monkeypatch.setattr(config, "JWT_AUDIENCE", None)

    with pytest.raises(ValueError) as exc_info:
        config.validate_jwt_config()
    
    assert "JWT_ISSUER" in str(exc_info.value)
    assert "JWT_AUDIENCE" in str(exc_info.value)

def test_validate_jwt_config_fails_when_audience_is_missing(monkeypatch):
    monkeypatch.setattr(config, "JWT_PUBLIC_KEY", "test-public-key")
    monkeypatch.setattr(config, "JWT_ISSUER", "nowarie-test")
    monkeypatch.setattr(config, "JWT_AUDIENCE", None)

    with pytest.raises(ValueError, match="JWT_AUDIENCE"):
        config.validate_jwt_config()

def test_load_public_key_fails_when_file_does_not_exist(monkeypatch, tmp_path):
    missing_key_path = tmp_path / "missing_key.pem"

    monkeypatch.setattr(config.os, "getenv", lambda name, default=None: (
        str(missing_key_path) if name == "JWT_PUBLIC_KEY_PATH" else default
    ))

    with pytest.raises(RuntimeError, match="JWT public key file not found"): config.load_public_key()
