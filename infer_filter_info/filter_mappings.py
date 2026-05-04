"""
Some utility functions and variables called throughout
"""
import numpy as np
from astropy import units as u
from astroquery.svo_fps import SvoFps
import os
import re
import json

from .exceptions import MissingDefaultError
from .util import DATADIR, NP_TRAPZ_FN

class Filter:
    def __init__(self, filter_name:str, telescope:str=None, instrument:str=None, out_wave_unit:u.Unit=u.AA):
        self.filter_name = filter_name
        self._telescope = telescope
        self._instrument = instrument
        self.out_wave_unit = out_wave_unit
        
        if self.telescope is None and self.instrument is None:
            self._telescope, self._instrument, self.filter_name = self.infer_telescope_instrument()
        
        if self.telescope is None:
            self._telescope, self.filter_name = self.infer_telescope()

        if self.instrument is None:
            self._instrument, self.filter_name = self.infer_instrument()
            
        self._svo_filter_id = f"{self._telescope}/{self._instrument}.{self.filter_name}"
            
        self.wave_eff = self.get_central_wave()
        self.sens = self.get_sens()

    @property
    def svo_filter_id(self):
        return self._svo_filter_id

    @svo_filter_id.setter
    def svo_filter_id(self, value):
        self._svo_filter_id = value
        self.sens = self.get_sens()
        self.wave_eff = self.get_central_wave()
        
    @property
    def telescope(self):
        return self._telescope

    @telescope.setter
    def telescope(self, val):
        self._telescope = val
        self.svo_filter_id = f"{self._telescope}/{self._instrument}.{self.filter_name}"

    @property
    def instrument(self):
        return self._instrument

    @instrument.setter
    def instrument(self, val):
        self._instrument = val
        self.svo_filter_id = f"{self._telescope}/{self._instrument}.{self.filter_name}"
        
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
        _RADIO_BANDS_PATH = DATADIR.joinpath("radio_bands.json")
        _RADIO_BANDS_DEFAULTS = DATADIR.joinpath("radio_default_telescopes.json")
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

    # Pattern explanation:
    # - Group 1: lower_value (number, can be int or float)
    # - Group 2: lower_unit (keV or MeV, optional)
    # - Group 3: upper_value (number, can be int or float)
    # - Group 4: upper_unit (keV or MeV)
    FILTER_NAME_PATTERN = re.compile(
        r'^(\d+(?:\.\d+)?)\s*(keV|MeV)?\s*-\s*(\d+(?:\.\d+)?)\s*(keV|MeV)$'
    )

    def __init__(
            self,
            filter_name:str,
            telescope:str=None,
            instrument:str=None,
            out_wave_unit:u.Unit=u.AA
    ):
        _XRAY_FILTERS_PATH = DATADIR.joinpath("xray_bands.json")
        _INSTRUMENT_MAP_PATH = DATADIR.joinpath("xray_telescope_to_instrument.json")
        _TELESCOPE_MAP_PATH = DATADIR.joinpath("xray_instrument_to_telescope.json")
        
        with open(_XRAY_FILTERS_PATH, "r") as f:
            self.XRAY_FILTERS = json.load(f)

        with open(_INSTRUMENT_MAP_PATH, "r") as f:
            self._INSTRUMENT_MAP = json.load(f)

        with open(_TELESCOPE_MAP_PATH, "r") as f:
            self._TELESCOPE_MAP = json.load(f)

        self.filter_name = filter_name
        self._og_lower_unit = None
        self._og_upper_unit = None
        self.lower_energy_keV, self.upper_energy_keV = self._validate_and_parse_filter_name(filter_name)
            
        super().__init__(filter_name, telescope, instrument, out_wave_unit=out_wave_unit)
        
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
            raise MissingDefaultError(f"Missing default telescope for {self.instrument} {self.filter_name}! Please either provide telescope name or append to  RADIO_TELESCOPE_DEFAULTS variable!") from exc

    def infer_telescope_instrument(self):
        """
        This infers the UVOIR telescope and instrument just based on the filter name
        """
        try:
            return self.XRAY_FILTERS[self.filter_name][:-1] # the last item is the effective energy, which we skip in this method
        except KeyError as exc:
            raise MissingDefaultError(f"Missing default telescope for {self.filter_name}! Please either provide telescope name, instrument name or append to  FILTER_DEFAULTS variable!") from exc        

    def get_central_wave(self):
        # X-ray effective energies are normally computed using the geomtric mean of the
        # energy range
        return ((self.lower_energy_keV*self.upper_energy_keV)**0.5 * u.keV).to(
            self.out_wave_unit, equivalencies=u.spectral()
        ).value

    def get_sens(self, n=100):
        min_wav, max_wav = self._xray_to_wave()
        return np.array([
            np.linspace(min_wav, max_wav, n),
            np.ones(n)
        ])
        
    def _xray_to_wave(self):
        wave1 = (self.upper_energy_keV * u.keV).to(
            self.out_wave_unit,
            equivalencies=u.spectral()
        ).value
        wave2 = (self.lower_energy_keV *  u.keV).to(
            self.out_wave_unit,
            equivalencies=u.spectral()
        ).value

        if wave1 > wave2:
            wave_min, wave_max = wave2, wave1
        else:
            wave_min, wave_max = wave1, wave2
        
        return wave_min, wave_max

    def _validate_and_parse_filter_name(self, filter_name: str) -> tuple[float, float]:
        """
        Validate and parse filter name into energy bounds.
        
        Args:
            filter_name: The filter name string to validate.
            
        Returns:
            Tuple of (lower_energy_keV, upper_energy_keV).
            
        Raises:
            ValueError: If format is invalid or energy bounds are illogical.
        """
        if not isinstance(filter_name, str):
            raise ValueError(f"filter_name must be a string, got {type(filter_name).__name__}")
        
        filter_name = filter_name.strip()
        
        match = self.FILTER_NAME_PATTERN.match(filter_name)
        if not match:
            raise ValueError(
                f"Invalid filter_name format: '{filter_name}'. "
                f"Expected format: '<number>[unit]-<number><unit>' "
                f"(e.g., '0.2-12keV', '0.2-10keV', '100keV-10MeV')"
            )
        
        lower_value = float(match.group(1))
        lower_unit_str = match.group(2)
        upper_value = float(match.group(3))
        upper_unit_str = match.group(4)
        
        # If lower unit is not specified, use the upper unit
        if lower_unit_str is None:
            if upper_unit_str is None:
                raise ValueError(
                    f"Invalid filter_name format: '{filter_name}'. "
                    f"At least one unit must be specified."
                )
            lower_unit_str = upper_unit_str
        
        lower_unit = u.Unit(lower_unit_str)
        upper_unit = u.Unit(upper_unit_str)
        
        # Store the original units
        self._og_lower_unit = lower_unit
        self._og_upper_unit = upper_unit
        
        # Convert both to keV for comparison and storage
        lower_keV = (lower_value * lower_unit).to(u.keV).value
        upper_keV = (upper_value * upper_unit).to(u.keV).value
        
        if lower_keV >= upper_keV:
            raise ValueError(
                f"Invalid energy range in '{filter_name}': "
                f"lower bound ({lower_value}{lower_unit} = {lower_keV}keV) "
                f"must be less than upper bound ({upper_value}{upper_unit} = {upper_keV}keV)"
            )
        
        return lower_keV, upper_keV
    
class UvoirFilter(Filter):

    def __init__(self, filter_name:str, telescope:str=None, instrument:str=None, out_wave_unit:u.Unit=u.AA, magsys=None):
        # some private paths to json data
        _FILTER_DEFAULTS_PATH = DATADIR.joinpath("filter_defaults.json")
        _INSTRUMENT_MAP_PATH = DATADIR.joinpath("telescope_to_instrument.json")
        _TELESCOPE_MAP_PATH = DATADIR.joinpath("instrument_to_telescope.json")
        _DEFAULT_MAGSYS_PATH = DATADIR.joinpath("default_magsys_map.json")
        
        # then read these files in to constants for the package
        with open(_FILTER_DEFAULTS_PATH, "r") as f:
            self.FILTER_DEFAULTS = json.load(f)

        with open(_INSTRUMENT_MAP_PATH, "r") as f:
            self._INSTRUMENT_MAP = json.load(f)

        with open(_TELESCOPE_MAP_PATH, "r") as f:
            self._TELESCOPE_MAP = json.load(f)

        with open(_DEFAULT_MAGSYS_PATH, "r") as f:
            self._DEFAULT_MAGSYS = json.load(f)
            
        super().__init__(filter_name, telescope, instrument, out_wave_unit=out_wave_unit)

        self.magsys = magsys
        if self.magsys is None:
            # default to AB? Reasonable assumption? Maybe we throw a warning here?
            self.magsys = self._DEFAULT_MAGSYS.get(self.filter_name, "AB")
            
        
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
            raise MissingDefaultError(f"Missing default telescope for {self.instrument} {self.filter_name}! Please either provide telescope name or append to  RADIO_TELESCOPE_DEFAULTS variable!") from exc

    def infer_telescope_instrument(self):
        """
        This infers the UVOIR telescope and instrument just based on the filter name
        """
        try:
            return self.FILTER_DEFAULTS[self.filter_name]
        except KeyError as exc:
            raise MissingDefaultError(f"Missing default telescope for {self.filter_name}! Please either provide telescope name, instrument name or append to  FILTER_DEFAULTS variable!") from exc

    def get_central_wave(self):
        wav, T = self.get_sens()
        wav_eff = NP_TRAPZ_FN(wav*T, wav)/NP_TRAPZ_FN(T, wav)
        return wav_eff

    def get_sens(self):
        transmission_table = SvoFps.get_transmission_data(self._svo_filter_id)
        wave = (
            transmission_table["Wavelength"].data.data * transmission_table["Wavelength"].unit
        ).to(self.out_wave_unit).value
        transmission = transmission_table["Transmission"].data.data
        return np.array([wave, transmission])
