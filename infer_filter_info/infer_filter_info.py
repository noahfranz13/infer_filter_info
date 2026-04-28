"""
The main user facing code of this package with the function to infer the filter info
"""

from .filter_mappings import (
    FilterMapping,
    UvoirFilterMapping,
    RadioFilterMapping,
    XrayFilterMapping
)
from .exceptions import InvalidObsTypeError

import numpy as np
from astropy import units as u
from astroquery.svo_fps import SvoFps

def infer_filter_info(
        filter_name:str,
        telescope:str=None,
        instrument:str=None,
        obs_type:str="uvoir",
        uvoir_defaults:UvoirFilterMapping=None,
        radio_defaults:RadioFilterMapping=None,
        xray_defaults:XrayFilterMapping=None
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
        uvoir_defaults (UvoirFilterMapping): The class with the default mappings for
                                             UV/Optical/IR. Default is the default
                                             mappings.
        radio_defaults (RadioFilterMapping): The class with the default mappings for
                                             Radio bands. Default is the default
                                             mappings.
        xray_defaults (XrayFilterMapping): The class with the default mappings for
                                             UV/Optical/IR. Default is the default
                                             mappings.

    Returns:
        A tuple of a float with the effective wavelength and the transmission curve as
        a 2 dimensional numpy array (first column is wavelength, second is
        transmission).
    """
    if uvoir_defaults is None:
        uvoir_defaults = UvoirFilterMappings()
    if radio_defaults is None:
        radio_defaults = RadioFilterMapping()
    if xray_defaults is None:
        xray_defaults = XrayFilterMapping()
        
    if obs_type == "uvoir":
        return _infer_uvoir(filter_name, telescope, instrument, uvoir_defaults)
    elif obs_type == "radio":
        return _infer_radio(filter_name, telescope, instrument, radio_defaults)
    elif obs_type == "xray":
        return _infer_xray(filter_name, telescope, instrument, xray_defaults)
    else:
        raise InvalidObsTypeError()

def _infer_uvoir(filter_name, telescope, instrument, defaults):
    """This first queries the SVO Filter Profile service using astroquery and then
    if the filter_name, telescope, instrument combo is not found it raises a warning
    and uses the defaults from FILTER_DEFAULTS. 
    """
    pass

def _infer_radio(filter_name, telescope, instrument, defaults):
    """This reads from the util.RADIO_BANDS dictionary for the effective wavelength and
    converts it to a wavelength astropy quantity, it also assumes a uniform transmission
    function (for now)
    """
    pass

def _infer_xray(filter_name, telescope, instrument, defaults):
    """This reads from the util.XRAY_FILTERS dictionary for the effective wavelength
    and assumes a uniform transmission function (for now)
    """
    pass
