"""
The main user facing code of this package with the function to infer the filter info
"""

from .filter_mappings import (
    Filter,
    UvoirFilter,
    RadioFilter,
    XrayFilter
)
from .exceptions import InvalidObsTypeError

import numpy as np
from astropy import units as u

def infer_filter_info(
        filter_name:str,
        telescope:str=None,
        instrument:str=None,
        obs_type:str="uvoir",
        out_wave_unit:u.Unit = u.AA
) -> (u.Quantity,np.ndarray):
    """
    Infer information about an astronomical photometric filter based on the filter name,
    telescope (optionally), and instrument (optionally). If the filter is not recognized
    or the telescope/instrument are not provided then we will assume the defaults
    defined in util.FILTER_DEFAULTS.

    Args:
        filter_name (str): The filter name. For example, "r" or "g" or "V". This can
                           also handle non-UV/Optical/IR filters (like radio bands).
                           See the obs_type keyword.
        telescope (str): The telescope name. This should be case insensitive.
        instrument (str): The instrument name. This should also be case insensitive.
        obs_type (str): Either "uvoir" for UV/Optical/IR filters, in which we will rely
                        on the SVO Filter Profile Service, or "radio", or "xray". 
        out_wave_unit (astropy.units.Unit): An astropy wavelength or frequency unit 
    Returns:
        A tuple of a float with the effective wavelength and the transmission curve as
        a 2 dimensional numpy array (first column is wavelength, second is
        transmission).
    """
            
    if obs_type == "uvoir":
        filt = UvoirFilter(
            filter_name,
            telescope=telescope,
            instrument=instrument,
            out_wave_unit=out_wave_unit
        )
    elif obs_type == "radio":
        filt = RadioFilter(
            filter_name,
            telescope=telescope,
            out_wave_unit=out_wave_unit
        )
    elif obs_type == "xray":
        filt = XrayFilter(
            filter_name,
            telescope=telescope,
            instrument=instrument,
            out_wave_unit=out_wave_unit
        )
    else:
        raise InvalidObsTypeError()

    return filt.wave_eff, filt.sens
