import glob

import pytest

from receptionist.config import WEEKDAYS, load_config

EXAMPLE_CONFIG_PATHS = ["business.example.yaml"] + sorted(
    glob.glob("examples/niches/*.yaml")
)


@pytest.mark.parametrize("path", EXAMPLE_CONFIG_PATHS)
def test_example_config_loads_and_validates(path):
    config = load_config(path)

    assert config.business.name
    assert config.business.greeting
    assert set(config.hours) == set(WEEKDAYS)
    assert len(config.faqs) >= 1
    assert len(config.departments) >= 1


def test_at_least_one_example_config_per_niche_found():
    # Guards against a glob/path typo silently matching nothing.
    assert len(EXAMPLE_CONFIG_PATHS) >= 6
