from bat_symphony.learner.validator import Validator
from bat_symphony.config import Config
from unittest.mock import MagicMock


def test_parse_validation_valid():
    cfg = Config()
    v = Validator(cfg, MagicMock(), MagicMock())
    result = v._parse_validation('{"valid": true, "reason": "looks good", "confidence": 0.9}')
    assert result["valid"] is True
    assert result["confidence"] == 0.9


def test_parse_validation_invalid_json():
    cfg = Config()
    v = Validator(cfg, MagicMock(), MagicMock())
    result = v._parse_validation("not json at all")
    assert result["valid"] is False
