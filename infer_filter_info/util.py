from importlib.resources import files
from astropy.utils.introspection import minversion
import numpy as np

if minversion(np, "2.0.0"):
    NP_TRAPZ_FN = np.trapezoid
else:
    NP_TRAPZ_FN = np.trapz # np.trapz is deprecated in numpy >2.0.0 

DATADIR = files("infer_filter_info").joinpath("data")
