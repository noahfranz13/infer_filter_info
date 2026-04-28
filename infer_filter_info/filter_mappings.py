"""
Some utility functions and variables called throughout
"""
import numpy as np
from astropy import units as u
import os
import json

from .exceptions import MissingDefaultError

class FilterMapping(object):
    pass

class RadioFilterMapping(FilterMapping):
    def __init__(self):
        _RADIO_BANDS_PATH = os.path.join("data", "radio_bands.json")
        _RADIO_BANDS_DEFAULTS = os.path.join("data", "radio_default_telescopes.json")
        with open(_RADIO_BANDS_PATH, "r") as f:
            self.RADIO_BANDS = json.load(f)
        with open(_RADIO_BANDS_DEFAULTS, "r") as f:
            self.RADIO_TELESCOPE_DEFAULTS = json.load(f)
            
    def infer_telescope(self, filter_name):
        try:
            return self.RADIO_TELESCOPE_DEFAULTS[filter_name]
        except KeyError as exc:
            raise MissingDefaultError(f"Missing default telescope for {filter_name}! Please either provide telescope name or append to  RADIO_TELESCOPE_DEFAULTS variable!") from exc
        
    def get_central_wave(self, filter_name):
        return (
            sum(self.RADIO_BANDS[telescope][filter_name])/2 * u.GHz
        ).to(u.nm, equivalencies=u.spectral())
    def get_sens(self, filter_name, n=100):
        min_freq, max_freq = self.RADIO_BANDS[telescope][filter_name]
        min_wav, max_wav = (
            (max_freq*u.GHz).to(u.nm, equivalencies=u.spectral()),
            (min_freq*u.GHz).to(u.nm, equivalencies=u.spectral())
        )
        return np.array([
            np.linspace(min_wav, max_wav, n),
            np.ones(n)
        ])
                    
class XrayFilterMapping(FilterMapping):
    def __init__(self):
        _XRAY_FILTERS_PATH = os.path.join("data", "xray_filters.json")
        with open(_XRAY_FILTERS_PATH, "r") as f:
            self.XRAY_FILTERS = json.load(f)
    
class UvoirFilterMapping(FilterMapping):

    def __init__(self):
        # some private paths to json data
        _FILTER_DEFAULTS_PATH = os.path.join("data", "filter_defaults.json")
        _INSTRUMENT_MAP_PATH = os.path.join("data", "instrument_to_telescope.json")
        _TELESCOPE_MAP_PATH = os.path.join("data", "telescope_to_instrument.json")

        # then read these files in to constants for the package
        with open(_FILTER_DEFAULTS_PATH, "r") as f:
            self.FILTER_DEFAULTS = json.load(f)

        with open(_INSTRUMENT_MAP_PATH, "r") as f:
            self._INSTRUMENT_MAP = json.load(f)

        with open(_TELESCOPE_MAP_PATH, "r") as f:
            self._TELESCOPE_MAP = json.load(f)

    # Define some other utility functions
    def infer_instrument(self, filter_name:str, telescope:str) -> str:
        """
        This infers an instrument from a combination of the filter_name and telescope

        Args:
            filter_name (str): A string of the filter name
            telescope (str): A string for the telescope name
        Returns:
            The inferred instrument name for querying the SVO FPS
        """
        try:
            return self._INSTRUMENT_MAP[telescope][filter_name]
        except KeyError as exc:
            raise MissingDefaultError(f"Missing default telescope for {telescope} {filter_name}! Please either provide instrument name or append to  RADIO_TELESCOPE_DEFAULTS variable!") from exc

    def infer_telescope(self, filter_name:str, instrument:str) -> str:
        """
        This infers a telescope from a combination of the filter_name and instrument

        Args:
            filter_name (str): A string of the filter name
            instrument (str): A string for the telescope name
        Returns:
            The inferred telescope name for querying the SVO FPS
        """
        try:
            return self._TELESCOPE_MAP[instrument][filter_name]
        except KeyError as exc:
            raise MissingDefaultError(f"Missing default telescope for {instrument} {filter_name}! Please either provide telescope name or append to  RADIO_TELESCOPE_DEFAULTS variable!") from exc

    def infer_telescope_instrument(self, filter_name:str):
        """
        This infers the UVOIR telescope and instrument just based on the filter name
        """
        try:
            return self.FILTER_DEFAULTS[filter_name]
        except KeyError as exc:
            raise MissingDefaultError(f"Missing default telescope for {filter_name}! Please either provide telescope name, instrument name or append to  FILTER_DEFAULTS variable!") from exc
