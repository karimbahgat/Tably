#!/usr/bin/env python

"""
This module contains the Table object.
"""
try:
    from collections import OrderedDict
except ImportError: # pragma: no cover
    from ordereddict import OrderedDict

from .columns import ColumnMapping, NumberType 
from .exceptions import ColumnDoesNotExistError, UnsupportedOperationError
from .rows import RowSequence, Row

class BaseTable(object):
    """
    A dataset consisting of rows and columns.

    :param rows: The data as a sequence of any sequences: tuples, lists, etc.
    :param column_types: A sequence of instances of:class:`.ColumnType`,
        one per column of data.
    :param column_names: A sequence of strings that are names for the columns.

    :var columns: A :class:`.ColumnMapping` for accessing the columns in this
        table.
    :var rows: A :class:`.RowSequence` for accessing the rows in this table.
    """
    def __init__(self, rows, column_names, column_types):
        len_column_types = len(column_types)
        len_column_names = len(column_names)

        if len_column_types != len_column_names:
            raise ValueError('column_types and column_names must be the same length.')

        if len(set(column_names)) != len_column_names:
            raise ValueError('Duplicate column names are not allowed.')

        self._column_types = tuple(column_types)
        self._column_names = tuple(column_names)
        self._cached_columns = {}
        self._cached_rows = {}

        cast_data = []

        cast_funcs = [c.cast for c in self._column_types]

        for i, row in enumerate(rows):
            if len(row) != len_column_types:
                raise ValueError('Row %i has length %i, but Table only has %i columns.' % (i, len(row), len_column_types))

            # Forked tables can share data (because they are immutable)
            # but original data should be buffered so it can't be changed
            if isinstance(row, Row):
                cast_data.append(row)

                continue

            cast_data.append(tuple(cast_funcs[i](d) for i, d in enumerate(row)))
        
        self._data = tuple(cast_data) 

    def _get_column(self, i):
        """
        Get a Column of data, caching a copy for next request.
        """
        if i not in self._cached_columns:
            column_type = self._column_types[i]

            self._cached_columns[i] = column_type.create_column(self, i)

        return self._cached_columns[i]

    def _get_row(self, i):
        """
        Get a Row of data, caching a copy for the next request.
        """
        if i not in self._cached_rows:
            # If rows are from a fork, they are safe to access directly
            if isinstance(self._data[i], Row):
                self._cached_rows[i] = self._data[i]
            else:
                self._cached_rows[i] = Row(self, i)

        return self._cached_rows[i]

    def _fork(self, rows, column_types=[], column_names=[]):
        """
        Create a new table using the metadata from this one.
        Used internally by functions like :meth:`order_by`.
        """
        if not column_types:
            column_types = self._column_types

        if not column_names:
            column_names = self._column_names

        return BaseTable(rows, column_names, column_types)

class NullOrder(object):
    """
    Dummy object used for sorting in place of None.

    Sorts as "greater than everything but other nulls."
    """
    def __lt__(self, other):
        return False 

    def __gt__(self, other):
        if other is None:
            return False

        return True


