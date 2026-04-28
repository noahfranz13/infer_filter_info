"""
Custom exceptions for the infer_filter_info package
"""

class InvalidObsTypeError(Exception):
    """
    Exception thrown when the user passes an invalid obs_type
    """

    def __str__(self):
        return "The input obs_type is invalid. It should either be 'xray', 'uvoir', or 'radio'"
