"""
Some utility functions and variables called throughout
"""
import os
import json

class FilterMapping(object):
    pass

class RadioFilterMapping(FilterMapping):
    def __init__(self):
        _RADIO_BANDS_PATH = os.path.join("data", "radio_bands.json")
        with open(_RADIO_BANDS_PATH, "r") as f:
            self.RADIO_BANDS = json.load(f)

class XrayFilterMapping(FilterMapping):
    def __init__(self):
        _XRAY_FILTERS_PATH = os.path.join("data", "xray_filters.json")
        with open(_XRAY_FILTERS_PATH, "r") as f:
            self.XRAY_FILTERS = json.load(f)
    
class UvoirFilterMapping(FilterMapping):

    def __init__(self):
        # some private paths to json data
        _FILTER_DEFAULTS_PATH = os.path.join("data", "filter_defaults.json")
        _INSTRUMENT_MAP_PATH = os.path.join("data", "instrument_map.json")
        _TELESCOPE_MAP_PATH = os.path.join("data", "telescope_map.json")

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
        return _INSTRUMENT_MAP[telescope][filter_name]

    def infer_telescope(self, filter_name:str, instrument:str) -> str:
        """
        This infers a telescope from a combination of the filter_name and instrument

        Args:
            filter_name (str): A string of the filter name
            instrument (str): A string for the telescope name
        Returns:
            The inferred telescope name for querying the SVO FPS
        """
        return _TELESCOPE_MAP[instrument][filter_name]
