"""
Some utility functions and variables called throughout
"""
import numpy as np
from astropy import units as u
from astroquery.svo_fps import SvoFps
import os
import json

from .exceptions import MissingDefaultError

DATADIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),"data")

class Filter:
    def __init__(self, filter_name:str, telescope:str=None, instrument:str=None, out_wave_unit:u.Unit=u.AA):
        self.filter_name = filter_name
        self.telescope = telescope
        self.instrument = instrument
        self.out_wave_unit = out_wave_unit
        
        if self.telescope is None and self.instrument is None:
            self.telescope, self.instrument, self.filter_name = self.infer_telescope_instrument()
        
        if self.telescope is None:
            self.telescope, self.filter_name = self.infer_telescope()

        if self.instrument is None:
            self.instrument, self.filter_name = self.infer_instrument()
            
        self._svo_filter_id = f"{self.telescope}/{self.instrument}.{self.filter_name}"
            
        self.wave_eff = self.get_central_wave()
        self.sens = self.get_sens()

    def infer_instrument(self):
        return None, self.filter_name

    def infer_telescope(self):
        return None, self.filter_name

    def infer_telescope_instrument(self):
        return None, None, self.filter_name
    
    def get_central_wave(self):
        raise NotImplementedError()

    def get_sens(self):
        raise NotImplementedError()
        
class RadioFilter(Filter):
    def __init__(self, filter_name:str, telescope:str=None, out_wave_unit:u.Unit=u.AA):
        _RADIO_BANDS_PATH = os.path.join(DATADIR, "radio_bands.json")
        _RADIO_BANDS_DEFAULTS = os.path.join(DATADIR, "radio_default_telescopes.json")
        with open(_RADIO_BANDS_PATH, "r") as f:
            self.RADIO_BANDS = json.load(f)
        with open(_RADIO_BANDS_DEFAULTS, "r") as f:
            self.RADIO_TELESCOPE_DEFAULTS = json.load(f)
        
        super().__init__(filter_name, telescope, out_wave_unit=out_wave_unit)
            
    def infer_telescope(self):
        try:
            return self.RADIO_TELESCOPE_DEFAULTS[self.filter_name]
        except KeyError as exc:
            raise MissingDefaultError(f"Missing default telescope for {self.filter_name}! Please either provide telescope name or append to  RADIO_TELESCOPE_DEFAULTS variable!") from exc
        
    def get_central_wave(self):
        return (
            sum(self.RADIO_BANDS[self.telescope][self.filter_name])/2 * u.GHz
        ).to(self.out_wave_unit, equivalencies=u.spectral())

    def get_sens(self, n=100):
        min_freq, max_freq = self.RADIO_BANDS[self.telescope][self.filter_name]
        min_wav, max_wav = (
            (max_freq*u.GHz).to(self.out_wave_unit, equivalencies=u.spectral()),
            (min_freq*u.GHz).to(self.out_wave_unit, equivalencies=u.spectral())
        )
        return np.array([
            np.linspace(min_wav, max_wav, n),
            np.ones(n)
        ])
                    
class XrayFilter(Filter):
    def __init__(self):
        _XRAY_FILTERS_PATH = os.path.join(DATADIR, "xray_filters.json")
        with open(_XRAY_FILTERS_PATH, "r") as f:
            self.XRAY_FILTERS = json.load(f)
                    
class UvoirFilter(Filter):

    def __init__(self, filter_name:str, telescope:str=None, instrument:str=None, out_wave_unit:u.Unit=u.AA):
        # some private paths to json data
        _FILTER_DEFAULTS_PATH = os.path.join(DATADIR, "filter_defaults.json")
        _INSTRUMENT_MAP_PATH = os.path.join(DATADIR, "telescope_to_instrument.json")
        _TELESCOPE_MAP_PATH = os.path.join(DATADIR, "instrument_to_telescope.json")
        
        # then read these files in to constants for the package
        with open(_FILTER_DEFAULTS_PATH, "r") as f:
            self.FILTER_DEFAULTS = json.load(f)

        with open(_INSTRUMENT_MAP_PATH, "r") as f:
            self._INSTRUMENT_MAP = json.load(f)

        with open(_TELESCOPE_MAP_PATH, "r") as f:
            self._TELESCOPE_MAP = json.load(f)

        super().__init__(filter_name, telescope, instrument, out_wave_unit=out_wave_unit)
        
    # Define some other utility functions
    def infer_instrument(self) -> str:
        """
        This infers an instrument from a combination of the filter_name and telescope

        Args:
            filter_name (str): A string of the filter name
            telescope (str): A string for the telescope name
        Returns:
            The inferred instrument name for querying the SVO FPS
        """
        try:
            return self._INSTRUMENT_MAP[self.telescope][self.filter_name], self.filter_name
        except KeyError as exc:
            raise MissingDefaultError(f"Missing default telescope for {self.telescope} {self.filter_name}! Please either provide instrument name or append to  TELESCOPE_DEFAULTS variable!") from exc

    def infer_telescope(self) -> str:
        """
        This infers a telescope from a combination of the filter_name and instrument

        Args:
            filter_name (str): A string of the filter name
            instrument (str): A string for the telescope name
        Returns:
            The inferred telescope name for querying the SVO FPS
        """
        try:
            return self._TELESCOPE_MAP[self.instrument][self.filter_name], self.filter_name
        except KeyError as exc:
            raise MissingDefaultError(f"Missing default telescope for {instrument} {filter_name}! Please either provide telescope name or append to  RADIO_TELESCOPE_DEFAULTS variable!") from exc

    def infer_telescope_instrument(self):
        """
        This infers the UVOIR telescope and instrument just based on the filter name
        """
        try:
            return self.FILTER_DEFAULTS[self.filter_name]
        except KeyError as exc:
            raise MissingDefaultError(f"Missing default telescope for {filter_name}! Please either provide telescope name, instrument name or append to  FILTER_DEFAULTS variable!") from exc

    def get_central_wave(self):
        wav, T = self.get_sens()
        wav_eff = np.trapezoid(wav*T, wav)/np.trapezoid(T, wav)
        return wav_eff

    def get_sens(self):
        transmission_table = SvoFps.get_transmission_data(self._svo_filter_id)
        wave = (
            transmission_table["Wavelength"].data.data * transmission_table["Wavelength"].unit
        ).to(self.out_wave_unit).value
        transmission = transmission_table["Transmission"].data.data
        return np.array([wave, transmission])
