import collections
import importlib
import re
from collections.abc import Hashable
from typing import Any

import numpy as np
from numpy.typing import NDArray
from sklearn.utils import parse_version  # noqa
from sklearn.utils import check_array


class LRUDict:
    """dict with limited capacity

    Using LRU eviction avoids memorizing a full dataset"""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = collections.OrderedDict()

    def __getitem__(self, key: Hashable):
        try:
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        except KeyError:
            return -1

    def __setitem__(self, key: Hashable, value: Any):
        try:
            self.cache.pop(key)
        except KeyError:
            if len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)
        self.cache[key] = value

    def __contains__(self, key: Hashable):
        return key in self.cache


def check_input(X) -> NDArray:
    """
    Check input with sklearn standards.
    Also converts X to a numpy array if not already.
    """
    # TODO check for weird type of input to pass scikit learn tests
    #  without messing with the original type too much

    X_ = check_array(
        X,
        dtype=None,
        ensure_2d=True,
        force_all_finite=False,
    )
    # If the array contains both NaNs and strings, convert to object type
    if X_.dtype.kind in {"U", "S"}:  # contains strings
        if np.any(X_ == "nan"):  # missing value converted to string
            return check_array(
                np.array(X, dtype=object),
                dtype=None,
                ensure_2d=True,
                force_all_finite=False,
            )

    return X_


def import_optional_dependency(name: str, extra: str = ""):
    """Import an optional dependency.

    By default, if a dependency is missing an ImportError with a nice
    message will be raised.

    Parameters
    ----------
    name : str
        The module name.
    extra : str
        Additional text to include in the ImportError message.

    Returns
    -------
    maybe_module : Optional[ModuleType]
        The imported module when found.
    """

    msg = (
        f"Missing optional dependency '{name}'. {extra} "
        f"Use pip or conda to install {name}."
    )
    try:
        module = importlib.import_module(name)
    except ImportError as exc:
        raise ImportError(msg) from exc

    return module


def parse_astype_error_message(e):
    """
    Parse the error message from a failed df.astype or pd.to_numeric call.
    """
    culprit = None
    if str(e).startswith("Given date string"):
        match = re.search(r"Given date string (.*?) not likely", str(e))
        if match:
            culprit = match.group(1)
    elif str(e).startswith("could not convert"):
        culprit = str(e).split(":")[1].strip()
    elif str(e).startswith("Unknown string format"):
        match = re.search(r"Unknown string format: (.*?) present at position", str(e))
        if match:
            culprit = match.group(1)
    elif str(e).startswith("Unable to parse string"):
        match = re.search(r"""Unable to parse string "(.*?)" at position""", str(e))
        if match:
            culprit = match.group(1)
    elif str(e).startswith("time data"):
        match = re.search(r"""time data "(.*?)" doesn't match format""", str(e))
        if match:
            culprit = match.group(1)
    return culprit
