import pytest

from receptionist.config import BusinessConfig, ConfigError, load_config


def test_load_example_config():
    config = load_config("business.example.yaml")
    assert config.business.name == "Sunrise Dental"
    assert config.hours["saturday"] is None
    assert config.hours["monday"].open == "09:00"
    assert len(config.faqs) >= 1
    assert len(config.departments) >= 1


def test_missing_file_raises_config_error(tmp_path):
    missing = tmp_path / "does_not_exist.yaml"
    with pytest.raises(ConfigError, match="not found"):
        load_config(missing)


def test_invalid_yaml_raises_config_error(tmp_path):
    bad_file = tmp_path / "business.yaml"
    bad_file.write_text("business: [this is not, a mapping")
    with pytest.raises(ConfigError):
        load_config(bad_file)


def test_missing_weekday_raises_clear_error(raw_config, tmp_path):
    del raw_config["hours"]["sunday"]
    bad_file = tmp_path / "business.yaml"
    _write_yaml(bad_file, raw_config)
    with pytest.raises(ConfigError, match="sunday"):
        load_config(bad_file)


def test_bad_time_format_raises_clear_error(raw_config, tmp_path):
    raw_config["hours"]["monday"]["open"] = "9am"
    bad_file = tmp_path / "business.yaml"
    _write_yaml(bad_file, raw_config)
    with pytest.raises(ConfigError, match="valid 24-hour time"):
        load_config(bad_file)


def test_bad_phone_number_raises_clear_error(raw_config):
    raw_config["departments"][0]["phone_number"] = "555-1234"
    with pytest.raises(Exception, match="E.164"):
        BusinessConfig.model_validate(raw_config)


def test_bad_timezone_raises_clear_error(raw_config):
    raw_config["business"]["timezone"] = "Mars/Olympus_Mons"
    with pytest.raises(Exception, match="IANA timezone"):
        BusinessConfig.model_validate(raw_config)


def test_department_lookup_case_insensitive(sample_config):
    dept = sample_config.department_by_name("billing")
    assert dept is not None
    assert dept.name == "Billing"
    assert sample_config.department_by_name("nope") is None


def _write_yaml(path, data):
    import yaml

    path.write_text(yaml.safe_dump(data))
