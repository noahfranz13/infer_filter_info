import pytest
import numpy as np
from astropy import units as u
from unittest.mock import patch, MagicMock
from infer_filter_info.infer_filter_info import infer_filter_info

@patch("infer_filter_info.filter_mappings.SvoFps.get_transmission_data")
def test_infer_filter_info_uvoir(mock_get_transmission_data):
    mock_table = MagicMock()
    mock_table.__getitem__.side_effect = lambda key: {
        "Wavelength": MagicMock(data=MagicMock(data=np.array([4000, 5000, 6000])), unit=u.AA),
        "Transmission": MagicMock(data=MagicMock(data=np.array([0, 1, 0])))
    }[key]
    mock_get_transmission_data.return_value = mock_table
    
    wave_eff, sens = infer_filter_info("r", telescope="Palomar", instrument="ZTF", obs_type="uvoir")
    assert np.isclose(wave_eff, 5000)
    assert sens.shape == (2, 3)

def test_infer_filter_info_radio():
    wave_eff, sens = infer_filter_info("L", telescope="VLA", obs_type="radio")
    expected_wave = (1.5 * u.GHz).to(u.AA, equivalencies=u.spectral())
    assert np.isclose(wave_eff.value, expected_wave.value)
    assert sens.shape == (2, 100)

def test_infer_filter_info_xray():
    with pytest.raises(NotImplementedError):
        infer_filter_info("soft", obs_type="xray")

def test_infer_filter_info_invalid_obs_type():
    from infer_filter_info.exceptions import InvalidObsTypeError
    with pytest.raises(InvalidObsTypeError):
        infer_filter_info("r", obs_type="gamma")

def test_infer_filter_info_out_wave_unit():
    wave_eff, sens = infer_filter_info("L", telescope="VLA", obs_type="radio", out_wave_unit=u.m)
    expected_wave = (1.5 * u.GHz).to(u.m, equivalencies=u.spectral())
    assert np.isclose(wave_eff.value, expected_wave.value)
    assert wave_eff.unit == u.m
    assert np.all(sens[0] < 1.0) # values in meters for 1.5GHz should be around 0.2m
