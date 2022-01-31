from __future__ import annotations

import dataclasses
import re
import typing

from pgquery.builder.actor import BuildingPayload
from pgquery.builder.clause import Renderable
from pgquery.builder.impl.column import BaseColumn, ColumnData
from pgquery.builder.impl.tokens import PGToken
from pgquery.builder.mixins.creation import SupportsCreation

# Pattern for converting CamelCase to snake_case
_camel2snake_convert_pattern = pattern = re.compile(r"(?<!^)(?=[A-Z])")


@dataclasses.dataclass
class TablePreferences:
    name: str
    if_not_exist: bool


class Table(SupportsCreation):

    __table_preferences__: TablePreferences
    __table_columns__: typing.Tuple[ColumnData, ...]

    def __init_subclass__(
        cls,
        title: typing.Optional[str] = None,
        if_not_exist: bool = True,
        **kwargs
    ):
        cls.__table_preferences__ = TablePreferences(
            name=cls._build_table_name(title),
            if_not_exist=if_not_exist,
        )
        cls.__table_columns__ = tuple(cls._parse_columns())
        return super().__init_subclass__(**kwargs)

    @classmethod
    def render_for_creation(cls, payload: BuildingPayload) -> None:
        payload.buffer << PGToken.CREATE_TABLE
        if cls.__table_preferences__.if_not_exist:
            payload.buffer << PGToken.WHITESPACE
            payload.buffer << PGToken.IF_NOT_EXIST

        # Render table name
        payload.buffer << PGToken.WHITESPACE
        payload.buffer << cls.__table_preferences__.name
        payload.buffer << PGToken.LEFT_PARENTHESIS

        columns_count = len(cls.__table_columns__)
        for ind, column in enumerate(cls.__table_columns__):
            column.render_for_table_creation(payload)
            # != Last column
            if columns_count - 1 != ind:
                payload.buffer << PGToken.COMMA

        payload.buffer << PGToken.RIGHT_PARENTHESIS

    @classmethod
    def _parse_columns(cls) -> typing.Generator[ColumnData, None, None]:
        for class_var_name, class_var_value in vars(cls).items():
            if isinstance(class_var_value, BaseColumn):
                full_column_data = ColumnData(
                    name=class_var_name, schema=class_var_value, table=cls
                )
                class_var_value.column_data = full_column_data
                yield full_column_data

    @classmethod
    def _build_table_name(cls, name: typing.Optional[str]) -> str:
        return _camel2snake_convert_pattern.sub(
            "_", name or cls.__name__
        ).lower()
