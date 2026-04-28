import pytest
from infer_filter_info.exceptions import InvalidObsTypeError, MissingDefaultError
from infer_filter_info.infer_filter_info import infer_filter_info

def test_invalid_obs_type_error():
    with pytest.raises(InvalidObsTypeError) as excinfo:
        infer_filter_info("r", obs_type="invalid")
    assert str(excinfo.value) == "The input obs_type is invalid. It should either be 'xray', 'uvoir', or 'radio'"

def test_missing_default_error():
    # This might require some setup to trigger MissingDefaultError
    # For example, a filter name that doesn't exist in defaults
    from infer_filter_info.filter_mappings import UvoirFilter
    with pytest.raises(MissingDefaultError):
        UvoirFilter("non_existent_filter")
