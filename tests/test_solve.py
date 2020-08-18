import os

import pytest

import darko as dk

conf_file = os.path.abspath('./tests/ConfigTest.xlsx')


@pytest.fixture
def config():
    """Generate some data for testing"""
    config = dk.load_config_excel(conf_file)
    assert isinstance(config, dict)
    return config


def test_build(config, tmpdir):
    # Using temp dir to ensure that each time a new directory is used
    config['SimulationDirectory'] = str(tmpdir)
    SimData = dk.build_simulation(config)
    assert isinstance(SimData, dict)  # how to test if sucessful build?


@pytest.mark.skipif('TRAVIS' in os.environ,
                    reason='This test is too long for the demo GAMS license version which is currently installed in Travis')
def test_solve_gams(config):
    # from darko.misc.gdx_handler import get_gams_path
    # r = dk.solve_GAMS(config['SimulationDirectory'], get_gams_path())
    r = dk.solve_GAMS(config['SimulationDirectory'])

    assert r
