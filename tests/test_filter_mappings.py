import pytest
import numpy as np
from astropy import units as u
from unittest.mock import patch, MagicMock
from infer_filter_info.filter_mappings import RadioFilter, UvoirFilter, Filter, XrayFilter
from infer_filter_info.exceptions import MissingDefaultError

def test_filter_base_class():
    # Filter is a base class with some NotImplementedError methods
    # But we can still test the __init__ logic if we provide telescope/instrument
    with patch.object(Filter, 'get_central_wave', return_value=5000*u.AA):
        with patch.object(Filter, 'get_sens', return_value=np.array([[5000],[1]])):
            f = Filter("r", telescope="Palomar", instrument="ZTF")
            assert f.filter_name == "r"
            assert f.telescope == "Palomar"
            assert f.instrument == "ZTF"
            assert f.svo_filter_id == "Palomar/ZTF.r"

def test_radio_filter():
    rf = RadioFilter("L", telescope="VLA")
    assert rf.filter_name == "L"
    assert rf.telescope == "VLA"
    # L band for VLA is 1-2 GHz. 
    # (1+2)/2 = 1.5 GHz. 
    # 1.5 GHz to AA: c / 1.5e9 Hz = 2.99792458e8 / 1.5e9 m = 0.19986 m = 1.9986e9 AA
    expected_wave = (1.5 * u.GHz).to(u.AA, equivalencies=u.spectral())
    assert rf.wave_eff.unit == u.AA
    assert np.isclose(rf.wave_eff.value, expected_wave.value)
    
    sens = rf.get_sens(n=10)
    assert sens.shape == (2, 10)
    assert np.all(sens[1] == 1.0) # Uniform transmission

def test_radio_filter_infer_telescope():
    rf = RadioFilter("L") # Should infer VLA from radio_default_telescopes.json
    assert rf.telescope == "VLA"
    assert rf.filter_name == "L"

def test_radio_filter_missing_default():
    with pytest.raises(MissingDefaultError):
        RadioFilter("non_existent_band")

@patch("infer_filter_info.filter_mappings.SvoFps.get_transmission_data")
def test_uvoir_filter(mock_get_transmission_data):
    # Mock return value for SvoFps.get_transmission_data
    # It returns an astropy Table-like object
    mock_table = MagicMock()
    mock_table.__getitem__.side_effect = lambda key: {
        "Wavelength": MagicMock(data=MagicMock(data=np.array([4000, 5000, 6000])), unit=u.AA),
        "Transmission": MagicMock(data=MagicMock(data=np.array([0, 1, 0])))
    }[key]
    mock_get_transmission_data.return_value = mock_table
    
    uf = UvoirFilter("r", telescope="Palomar", instrument="ZTF")
    assert uf.filter_name == "r"
    assert uf.telescope == "Palomar"
    assert uf.instrument == "ZTF"
    
    # wave_eff is calculated using trapezoid rule
    # wav = [4000, 5000, 6000], T = [0, 1, 0]
    # wav*T = [0, 5000, 0]
    # np.trapezoid([0, 5000, 0], [4000, 5000, 6000]) = (0.5 * (0+5000) * 1000) + (0.5 * (5000+0) * 1000) = 2500000 + 2500000 = 5000000
    # np.trapezoid([0, 1, 0], [4000, 5000, 6000]) = (0.5 * (0+1) * 1000) + (0.5 * (1+0) * 1000) = 500 + 500 = 1000
    # wave_eff = 5000000 / 1000 = 5000
    assert np.isclose(uf.wave_eff, 5000)
    
    sens = uf.get_sens()
    assert np.allclose(sens[0], [4000, 5000, 6000])
    assert np.allclose(sens[1], [0, 1, 0])

def test_uvoir_filter_infer_all():
    # Test inferring telescope and instrument from filter name
    # Using "g" which should be in filter_defaults.json as ["SLOAN", "SDSS", "g"]
    with patch("infer_filter_info.filter_mappings.SvoFps.get_transmission_data") as mock_get_transmission_data:
        mock_table = MagicMock()
        mock_table.__getitem__.side_effect = lambda key: {
            "Wavelength": MagicMock(data=MagicMock(data=np.array([4000, 5000, 6000])), unit=u.AA),
            "Transmission": MagicMock(data=MagicMock(data=np.array([0, 1, 0])))
        }[key]
        mock_get_transmission_data.return_value = mock_table
        
        uf = UvoirFilter("g")
        assert uf.telescope == "SLOAN"
        assert uf.instrument == "SDSS"
        assert uf.filter_name == "g"
        assert uf.svo_filter_id == "SLOAN/SDSS.g"

def test_uvoir_filter_magsys():
    with patch("infer_filter_info.filter_mappings.SvoFps.get_transmission_data") as mock_get_transmission_data:
        mock_table = MagicMock()
        mock_table.__getitem__.side_effect = lambda key: {
            "Wavelength": MagicMock(data=MagicMock(data=np.array([4000, 5000, 6000])), unit=u.AA),
            "Transmission": MagicMock(data=MagicMock(data=np.array([0, 1, 0])))
        }[key]
        mock_get_transmission_data.return_value = mock_table
        
        # Explicit magsys
        uf = UvoirFilter("g", magsys="vega")
        assert uf.magsys == "vega"
        
        # Default magsys from map (V -> vega)
        uf_v = UvoirFilter("V")
        assert uf_v.magsys == "vega"
        
        # Another from map (F280N -> A)
        uf_f280n = UvoirFilter("F280N")
        assert uf_f280n.magsys == "AB"
        
        # Fallback magsys (unknown filter with explicit telescope -> AB)
        uf_unknown = UvoirFilter("unknown_filter", telescope="Palomar", instrument="ZTF")
        assert uf_unknown.magsys == "AB"

def test_xray_filter_init():
    xf = XrayFilter("0.2-10keV", telescope="Swift", instrument="XRT")
    assert xf.filter_name == "0.2-10keV"
    assert xf.telescope == "Swift"
    assert xf.instrument == "XRT"
    assert xf.lower_energy_keV == 0.2
    assert xf.upper_energy_keV == 10.0
    
    # wave_eff = sqrt(0.2 * 10) = sqrt(2) = 1.4142... keV
    # 1.4142 keV to AA: h*c / E
    expected_energy = np.sqrt(0.2 * 10.0) * u.keV
    expected_wave = expected_energy.to(u.AA, equivalencies=u.spectral())
    assert np.isclose(xf.wave_eff, expected_wave.value)

def test_xray_filter_infer_all():
    # "0.2-10keV" is in xray_bands.json as ["Swift", "XRT", "0.2-10keV", 1.414]
    xf = XrayFilter("0.2-10keV")
    assert xf.telescope == "Swift"
    assert xf.instrument == "XRT"
    assert xf.filter_name == "0.2-10keV"

def test_xray_filter_get_sens():
    xf = XrayFilter("0.2-10keV", telescope="Swift", instrument="XRT")
    sens = xf.get_sens(n=5)
    assert sens.shape == (2, 5)
    # Energy 10 keV -> short wave, 0.2 keV -> long wave
    w1 = (10 * u.keV).to(u.AA, equivalencies=u.spectral()).value
    w2 = (0.2 * u.keV).to(u.AA, equivalencies=u.spectral()).value
    assert np.isclose(sens[0][0], w1)
    assert np.isclose(sens[0][-1], w2)
    assert np.all(sens[1] == 1.0)

def test_xray_filter_parsing_mixed_units():
    xf = XrayFilter("100keV-1MeV", telescope="INTEGRAL", instrument="IBIS (PICsIT layer)")
    assert xf.lower_energy_keV == 100.0
    assert xf.upper_energy_keV == 1000.0 # 1 MeV = 1000 keV

def test_xray_filter_invalid_format():
    with pytest.raises(ValueError, match="Invalid filter_name format"):
        XrayFilter("invalid-format")
    
    with pytest.raises(ValueError, match="Invalid filter_name format"):
        XrayFilter("0.2-10")

def test_xray_filter_illogical_range():
    with pytest.raises(ValueError, match="must be less than upper bound"):
        XrayFilter("10-2keV")

def test_xray_filter_missing_default():
    with pytest.raises(MissingDefaultError):
        XrayFilter("100-200keV") # Not in xray_bands.json

