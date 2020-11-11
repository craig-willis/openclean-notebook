# This file is part of the Data Cleaning Library (openclean).
#
# Copyright (C) 2018-2020 New York University.
#
# openclean is released under the Revised BSD License. See file LICENSE for
# full license details.

from abc import ABCMeta, abstractmethod

import pandas as pd

from typing import Dict, Optional

from openclean.data.types import Columns


class Profiler(metaclass=ABCMeta):  # pragma: no cover
    """Interface for data profiler that generate metadata for a given data
    frame.
    """
    @abstractmethod
    def profile(self, df: pd.DataFrame, columns: Optional[Columns] = None) -> Dict:
        """Run profiler on a given data frame. The structure of the resulting
        dictionary is implementatin dependent.

        TODO: define required components in the result of a data profier.

        Parameters
        ----------
        df: pd.DataFrame
            Input data frame.
        columns: int, string, or list(int or string), default=None
            Single column or list of column index positions or column names for
            those columns that are being profiled. Profile the full dataset if
            None.

        Returns
        -------
        dict
        """
        raise NotImplementedError()
