# This file is part of the History Store (histore).
#
# Copyright (C) 2018-2020 New York University.
#
# The History Store (histore) is released under the Revised BSD License. See
# file LICENSE for full license details.

"""Implementation of the metadata store class that maintains metadata
information about dataset snapshots in main memory.
"""

from typing import Dict, Optional

from openclean_jupyter.metadata.metastore.base import MetadataStore


class VolatileMetadataStore(MetadataStore):
    """Metadata store that maintains annotations for a dataset snapshot in main
    memory. Metadata is not persistet in any other form and therefore volatile
    if the metadata store object is destroyed.
    """
    def __init__(self):
        """Initialize the dictionary that maintains metadata for identifiable
        components of a dataset.
        """
        self.metadata = dict()

    def read(
        self, column_id: Optional[int] = None, row_id: Optional[int] = None
    ) -> Dict:
        """Read the annotation dictionary for the specified object.

        Parameters
        ----------
        column_id: int, default=None
            Column identifier for the referenced object (None for rows or full
            datasets).
        row_id: int, default=None
            Row identifier for the referenced object (None for columns or full
            datasets).

        Returns
        -------
        dict
        """
        return self.metadata.get(KEY(column_id, row_id), dict())

    def write(
        self, doc: Dict, column_id: Optional[int] = None,
        row_id: Optional[int] = None
    ):
        """Write the annotation dictionary for the specified object.

        Parameters
        ----------
        doc: dict
            Annotation dictionary that is being written to file.
        column_id: int, default=None
            Column identifier for the referenced object (None for rows or full
            datasets).
        row_id: int, default=None
            Row identifier for the referenced object (None for columns or full
            datasets).

        Returns
        -------
        dict
        """
        self.metadata[KEY(column_id, row_id)] = doc
        return doc


# -- Helper functions ---------------------------------------------------------

def KEY(column_id: Optional[int] = None, row_id: Optional[int] = None) -> str:
    """Get the unque key for an identifiable object.

    Parameters
    ----------
    snapshot_id: int
        Unique snapshot version identifier.
    metadata_id: int
        Unique metadata object identifier.

    Returns
    -------
    string
    """
    if column_id is None and row_id is None:
        return 'ds'
    elif row_id is None:
        return 'col_{}'.format(column_id)
    elif column_id is None:
        return 'row_{}'.format(row_id)
    return 'cell_{}_{}'.format(column_id, row_id)
