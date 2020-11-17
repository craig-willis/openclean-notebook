# This file is part of the Data Cleaning Library (openclean).
#
# Copyright (C) 2018-2020 New York University.
#
# openclean is released under the Revised BSD License. See file LICENSE for
# full license details.

"""The openclean engine maintains a collection of datasets. Each dataset is
identified by a unique name. Dataset snapshots are maintained by a datastore.
"""

from histore.archive.manager.base import ArchiveManager
from histore.archive.manager.persist import PersistentArchiveManager
from histore.archive.manager.mem import VolatileArchiveManager
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
import os

from openclean.util.core import unique_identifier
from openclean_jupyter.controller.spreadsheet import spreadsheet
from openclean_jupyter.datastore.base import Datastore, Datasource, SnapshotHandle
from openclean_jupyter.datastore.cache import CachedDatastore
from openclean_jupyter.datastore.histore import HISTOREDatastore
from openclean_jupyter.engine.data import DataEngine
from openclean_jupyter.engine.library.command import CommandRegistry
from openclean_jupyter.engine.registry import registry
from openclean_jupyter.engine.store.base import ObjectRepository
from openclean_jupyter.metadata.metastore.base import MetadataStore
from openclean_jupyter.metadata.metastore.fs import FileSystemMetadataStoreFactory
from openclean_jupyter.metadata.metastore.mem import VolatileMetadataStoreFactory


class OpencleanEngine(object):
    """The idea of the engine is to wrap a set of datasets and provide additional
    functionality to show a spreadsheet view, register new commands, etc. Many
    of the methods for this class are direct copies of the methods that are
    implemented by the data store.

    Datasets that are created from files of data frames are maintained by an
    archive manager.

    Each engine has a unique identifier allowing a user to use multiple
    engines if necessary.
    """
    def __init__(
        self, identifier: str, manager: ArchiveManager, objects: ObjectRepository,
        basedir: Optional[str] = None, cached: Optional[bool] = True
    ):
        """Initialize the engine identifier and the manager for created dataset
        archives.

        Paramaters
        ----------
        identifier: string
            Unique identifier for the engine instance.
        manager: histore.archive.manager.base.ArchiveManager
            Manager for created dataset archives.
        objects: openclean_jupyter.engine.store.base.ObjectRepository
            Repository for objects (e.g., registered functions).
        basedir: string, default=None
            Path to directory on disk where archive metadata is maintained.
        cached: bool, default=True
            Flag indicating whether the all datastores that are created for
            existing archives are cached datastores or not.
        """
        self.identifier = identifier
        self.manager = manager
        self.basedir = basedir
        # Registry of commands that can be applied to the maintained datasets.
        self.register = CommandRegistry(store=objects)
        # Dictionary for the maintained datasets. Maintains data engines that
        # contain the archive identifier and references to the datastore and
        # the archive manager.
        # The identifier and manager are only set for persistent datasets to
        # allow dropping them.
        self._datasets = dict()
        # Initialize all archives that are maintained by the manager.
        for descriptor in self.manager.list():
            archive_id = descriptor.identifier()
            archive = self.manager.get(archive_id)
            if self.basedir is not None:
                metadir = os.path.join(self.basedir, archive_id)
                metastore = FileSystemMetadataStoreFactory(basedir=metadir)
            else:
                metastore = VolatileMetadataStoreFactory()
            datastore = HISTOREDatastore(archive=archive, metastore=metastore)
            if cached:
                # Wrapped datastore into a cached store if requested.
                datastore = CachedDatastore(datastore=datastore)
            self._datasets[descriptor.name()] = DataEngine(
                datastore=datastore,
                commands=self.register,
                identifier=archive_id,
                manager=self.manager,
                pk=descriptor.primary_key()
            )

    def checkout(
        self, name: str, version: Optional[int] = None
    ) -> pd.DataFrame:
        """Get a specific version of a dataset. The dataset is identified by
        the unique name and the dataset version by the unique version
        identifier.

        Raises a ValueError if the dataset or the given version are unknown.

        Parameters
        ----------
        name: string
            Unique dataset name.
        version: int
            Unique dataset version identifier.

        Returns
        -------
        pd.DataFrame

        Raises
        ------
        ValueError
        """
        return self._datastore(name=name).checkout(version=version)

    def commit(
        self, df: pd.DataFrame, name: str, action: Optional[Dict] = None
    ) -> pd.DataFrame:
        """Insert a new version for a dataset. If the dataset name is unknown a
        new dataset archive will be created.

        Parameters
        ----------
        df: pd.DataFrame
            Data frame containing the new dataset version that is being stored.
        name: string
            Unique dataset name.
        action: dict, default=None
            Optional description of the action that created the new dataset
            version.

        Returns
        -------
        pd.DataFrame
        """
        return self._datastore(name=name).commit(df=df, action=action)

    def create(
        self, source: Datasource, name: str,
        primary_key: Optional[Union[List[str], str]] = None,
        cached: Optional[bool] = True
    ) -> pd.DataFrame:
        """Create an initial dataset archive that is idetified by the given
        name. The given data represents the first snapshot in the created
        archive.

        Raises a ValueError if an archive with the given name already exists.

        Parameters
        ----------
        source: pd.DataFrame, CSVFile, or string
            Data frame or file containing the first version of the archived
            dataset.
        name: string
            Unique dataset name.
        primary_key: string or list, default=None
            Column(s) that are used to generate identifier for rows in the
            archive.
        cached: bool, default=True
            Flag indicating whether the last accessed dataset snapshot for
            the created dataset is cached for fast access.

        Returns
        -------
        pd.DataFrame

        Raises
        ------
        ValueError
        """
        # Ensure that the dataset name is unique.
        if name in self._datasets:
            raise ValueError("dataset '{}' exists".format(name))
        # Create a new dataset archive with the associated manager.
        descriptor = self.manager.create(name=name, primary_key=primary_key)
        archive_id = descriptor.identifier()
        archive = self.manager.get(archive_id)
        # Commit the given dataset to the archive.
        archive.commit(doc=source)
        # Create a datastore to manage the archive and register that datastore
        # with this engine under the given name.
        if self.basedir is not None:
            metadir = os.path.join(self.basedir, archive_id)
            metastore = FileSystemMetadataStoreFactory(basedir=metadir)
        else:
            metastore = VolatileMetadataStoreFactory()
        datastore = HISTOREDatastore(archive=archive, metastore=metastore)
        if cached:
            # Wrapped datastore into a cached store if requested.
            datastore = CachedDatastore(datastore=datastore)
        self._datasets[name] = DataEngine(
            datastore=datastore,
            commands=self.register,
            identifier=archive_id,
            manager=self.manager,
            pk=primary_key
        )
        # Checkout and return the data frame for the loaded datasets snapshot.
        return datastore.checkout()

    def dataset(self, name: str) -> DataEngine:
        """Get object that allows to run registered (column) commands on the
        current version of a dataset that is identified by its unique name.

        Parameters
        ----------
        name: string
            Unique dataset name.

        Returns
        -------
        openclean_jupyter.engine.data.DataEngine
        """
        return self._handle(name)

    def _datastore(self, name: str) -> Datastore:
        """Get the datastore for the dataset with the given name. Raises a
        ValueError if the dataset name is unknonw.

        Parameters
        ----------
        name: string
            Unique dataset name.

        Returns
        -------
        openclean_jupyter.datastore.base.Datastore

        Raises
        ------
        ValueError
        """
        return self._handle(name).datastore

    def drop(self, name: str):
        """Delete the full history for the dataset with the given name. Raises
        a ValueError if the dataset name is unknonw.

        Parameters
        ----------
        name: string
            Unique dataset name.

        Raises
        ------
        ValueError
        """
        self._handle(name).drop()
        del self._datasets[name]

    def edit(
        self, name: str, n: Optional[int] = None,
        random_state: Optional[Tuple[int, List]] = None
    ):
        """Display the spreadsheet view for a given dataset. The dataset is
        identified by its unique name. Raises a ValueError if no dataset with
        the given name exists.

        Creates a new data frame that contains a random sample of the rows in
        the last snapshot of the identified dataset. This sample is registered
        as a separate dataset with the engine. If neither n nor frac are
        specified a random sample of size 100 is generated.

        Parameters
        ----------
        name: string
            Unique dataset name.
        n: int, default=None
            Number of rows in the sample dataset.
        random_state: int or list, default=None
            Seed for random number generator.

        Raises
        ------
        ValueError
        """
        # Create a sample of size 100 if neither n nor frac is given.
        n = 100 if n is None else n
        # Get the handle for the referenced dataset and checkout the latest
        # dataset snapshot.
        handle = self._handle(name)
        df = self.checkout(name=name)
        # Create a random sample from the dataset. This is only necessary if
        # the dataset contains more rows than the sample size.
        if n < df.shape[0]:
            df = df.sample(n=n, random_state=random_state)
        # Register the generated sample as a new dataset using a volatile
        # archive manager. The name for the new dataset is a unique 16 character
        # string.
        sample_id = unique_identifier(16)
        while sample_id in self._datasets:
            sample_id = unique_identifier(16)
        manager = VolatileArchiveManager()
        descriptor = manager.create(name=sample_id, primary_key=handle.pk)
        archive_id = descriptor.identifier()
        archive = manager.get(archive_id)
        archive.commit(doc=df)
        datastore = HISTOREDatastore(
            archive=archive,
            metastore=VolatileMetadataStoreFactory()
        )
        # Use a cached datastore to speed-up access to the last datset version.
        datastore = CachedDatastore(datastore=datastore)
        # Do not include the manager in the handle for the created dataset. We
        # also include the identifier of the original dataset as a reference
        # for the source of a sampled dataset.
        ds = DataEngine(
            datastore=datastore,
            pk=handle.pk,
            original=handle
        )
        self._datasets[sample_id] = ds
        # Embed the spreadsheet view into the notebook.
        spreadsheet(name=sample_id, engine=self.identifier)

    def _handle(self, name: str) -> DataEngine:
        """Get the handle for the dataset with the given name. Raises a
        ValueError if the dataset name is unknonw.

        Parameters
        ----------
        name: string
            Unique dataset name.

        Returns
        -------
        openclean_jupyter.engine.data.DataEngine

        Raises
        ------
        ValueError
        """
        if name not in self._datasets:
            raise ValueError("unknown dataset '{}'".format(name))
        return self._datasets[name]

    def history(self, name: str) -> List[SnapshotHandle]:
        """Get list of snapshot handles for all versions of a given dataset.
        The datset is identified by the unique dataset name.

        Raises a ValueError if the dataset name is unknown.

        Parameters
        ----------
        name: string
            Unique dataset name.

        Returns
        -------
        list of openclean_jupyter.datastore.base.SnapshotHandle

        Raises
        ------
        ValueError
        """
        return self._datastore(name=name).snapshots()

    def load_dataset(
        self, source: Datasource, name: str,
        primary_key: Optional[Union[List[str], str]] = None,
        cached: Optional[bool] = True
    ) -> pd.DataFrame:
        """Create an initial dataset archive that is idetified by the given
        name. The given data frame represents the first snapshot in the created
        archive.

        Raises a ValueError if an archive with the given name already exists.

        This is a synonym for create() for backward compatibility.

        Parameters
        ----------
        source: pd.DataFrame or string
            Data frame or file containing the first version of the archived
            dataset.
        name: string
            Unique dataset name.
        primary_key: string or list, default=None
            Column(s) that are used to generate identifier for rows in the
            archive.
        cached: bool, default=True
            Flag indicating whether the last accessed dataset snapshot for
            the created dataset is cached for fast access.

        Returns
        -------
        pd.DataFrame

        Raises
        ------
        ValueError
        """
        return self.create(
            source=source,
            name=name,
            primary_key=primary_key,
            cached=cached
        )

    def metadata(
        self, name: str, version: Optional[int] = None
    ) -> MetadataStore:
        """Get metadata that is associated with the referenced dataset version.
        If no version is specified the metadata collection for the latest
        version is returned.

        Raises a ValueError if the dataset or the specified version is unknown.

        Parameters
        ----------
        name: string
            Unique dataset name.
        version: int
            Unique dataset version identifier.

        Returns
        -------
        openclean_jupyter.metadata.metastore.base.MetadataStore

        Raises
        ------
        ValueError
        """
        return self._datastore(name=name).metadata(version=version)


# -- Engine factory -----------------------------------------------------------

def DB(
    basedir: Optional[str] = None, create: Optional[bool] = False,
    cached: Optional[bool] = True
) -> OpencleanEngine:
    """Create an instance of the openclean-goes-jupyter engine. This test
    implementation uses HISTORE as the underlying datastore. All files will
    be stored in the given base directory. If no base directory is given, a
    volatile archive manager will be used instead of a persistent one.

    If the create flag is True all existing files in the base directory (if
    given) will be removed.

    Parameters
    ----------
    basedir: string
        Path to directory on disk where archives are maintained.
    create: bool, default=False
        Create a fresh instance of the archive manager if True. This will
        delete all files in the base directory.
    cached: bool, default=True
        Flag indicating whether the all datastores that are created for
        existing archives are cached datastores or not.

    Returns
    -------
    openclean_jupyter.engine.base.OpencleanEngine
    """
    # Create a unique identifier to register the created engine in the
    # global registry dictionary. Use an 8-character key here. Make sure to
    # account for possible conflicts.
    engine_id = unique_identifier(8)
    while engine_id in registry:
        engine_id = unique_identifier(8)
    # Create the engine components and the engine instance itself.
    if basedir is not None:
        histore = PersistentArchiveManager(basedir=basedir, create=create)
        metadir = os.path.join(basedir, '.metadata')
    else:
        histore = VolatileArchiveManager()
        metadir = None
    engine = OpencleanEngine(
        identifier=engine_id,
        manager=histore,
        basedir=metadir,
        cached=cached
    )
    # Register the new engine instance before returning it.
    registry[engine_id] = engine
    return engine
