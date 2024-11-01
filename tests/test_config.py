import glob
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from config import get_config

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")
print(EXAMPLES_DIR)


def test_configs():
    """
    Test all configuration files in the examples directory.
    """
    config_files = glob.glob(os.path.join(EXAMPLES_DIR, "*.yaml"))
    assert config_files, "No config files found in the examples directory"

    for config_file in config_files:
        try:
            config = get_config(config_file)
            assert config is not None, f"Config is None for file {config_file}"
        except Exception as e:
            pytest.fail(f"Validation failed for valid config file {config_file}: {e}")
