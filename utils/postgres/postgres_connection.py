import time
from dataclasses import is_dataclass, astuple
from typing import List, Tuple, Optional

import logging
import psycopg
import polars as pl
from psycopg import sql


class PostgresConnection:
    def __init__(self, url: str):
        self.logger = logging.getLogger(__name__)

        self.logger.info("opening postgres connection")
        self.connection: psycopg.Connection = psycopg.connect(url)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self):
        self.logger.info("closing postgres connection")
        if self.connection and not self.connection.closed:
            self.connection.close()

    @classmethod
    def dict_to_tuple(cls, dictionary: dict) -> tuple:
        return tuple(
            cls.dict_to_tuple(value) if isinstance(value, dict) else value
            for value in dictionary.values()
        )

    @classmethod
    def _adapt_composite(cls, value):
        if value is None:
            return None

        if isinstance(value, dict):
            return cls.dict_to_tuple(value)

        if isinstance(value, tuple):
            return value

        if is_dataclass(value):
            return astuple(value)

        if hasattr(value, "to_tuple"):
            return value.to_tuple()

        raise TypeError(f"can't adapt {type(value)} to composite")

    @classmethod
    def check_dataframe_writeable(
            cls,
            dataframe: pl.DataFrame,
            conflict_columns: List[str]
    ) -> Tuple[List[str], List[str]]:
        columns = dataframe.columns
        update_columns = [col for col in columns if col not in conflict_columns]

        if dataframe.is_empty():
            return [], []

        if not update_columns:
            return [], []

        return columns, update_columns

    @classmethod
    def _get_insert_query(
            cls,
            table_name: sql.Identifier,
            columns_list: sql.Template,
            values: Optional[sql.Composed],
            stage_table_name: Optional[sql.Identifier],
            conflict_clause: sql.Template,
            update_clause: sql.Composed
    ) -> sql.Composed:
        if values:
            body_clause = sql.SQL("""
            VALUES ({bind_arguments_str})
            """).format(
                bind_arguments_str=values
            )

        else:
            body_clause = sql.SQL("""
                                  SELECT {column_list_str}
                                  FROM {stage_table_name}
                                  """).format(
                column_list_str=columns_list,
                stage_table_name=stage_table_name
            )

        return sql.SQL(
            """
            INSERT INTO {table_name} ({column_list_str})
                {body_clause}
            ON CONFLICT ({conflict_clause_str}) DO
            UPDATE SET {update_clause_str}
            """
        ).format(
            table_name=table_name,
            column_list_str=columns_list,
            body_clause=body_clause,
            conflict_clause_str=conflict_clause,
            update_clause_str=update_clause
        )

    def _upsert_small_dataframe_dto_safe(
            self,
            dataframe: pl.DataFrame,
            table_name: str,
            conflict_columns: List[str]
    ):
        columns, update_columns = self.check_dataframe_writeable(dataframe, conflict_columns)
        if not update_columns or not columns:
            self.logger.warning("dataframe has no writeable data")
            return 0

        sql_operation = self._get_insert_query(
            table_name=sql.Identifier(table_name),
            columns_list=sql.SQL(", ").join(map(sql.Identifier, columns)),
            values=sql.SQL(", ").join(sql.Placeholder() * len(columns)),
            stage_table_name=None,
            conflict_clause=sql.SQL(", ").join(map(sql.Identifier, conflict_columns)),
            update_clause=sql.SQL(", ").join(
                sql.SQL("{col} = EXCLUDED.{col}").format(col=sql.Identifier(col))
                for col in update_columns
            )
        )

        with self.connection.transaction():
            with self.connection.cursor() as cursor:
                cursor.executemany(
                    sql_operation,
                    dataframe.rows()
                )

        return 0

    def _upsert_bulk_dataframe_dto_safe(
            self,
            dataframe: pl.DataFrame,
            table_name: str,
            conflict_columns: List[str]
    ):
        columns, update_columns = self.check_dataframe_writeable(dataframe, conflict_columns)
        if not update_columns or not columns:
            self.logger.warning("dataframe has no writeable data")
            return 0

        temp_table = sql.Identifier(f"_tmp_{table_name}")
        target_table = sql.Identifier(table_name)

        columns_sql = sql.SQL(", ").join(map(sql.Identifier, columns))
        with self.connection.transaction():
            with self.connection.cursor() as cursor:
                cursor.execute(sql.SQL(
                    """
                    CREATE
                    TEMP TABLE {temp_table} (LIKE {target_table} INCLUDING DEFAULTS)
                    ON COMMIT DROP
                    """
                ).format(temp_table=temp_table, target_table=target_table))

                copy_sql = sql.SQL("COPY {temp_table} ({columns}) FROM STDIN").format(temp_table=temp_table, columns=columns_sql)
                with cursor.copy(copy_sql) as copy:
                    for row in dataframe.rows():
                        copy.write_row(row)

                sql_operation = self._get_insert_query(
                    table_name=target_table,
                    columns_list=sql.SQL(", ").join(map(sql.Identifier, columns)),
                    values=None,
                    stage_table_name=temp_table,
                    conflict_clause=sql.SQL(", ").join(map(sql.Identifier, conflict_columns)),
                    update_clause=sql.SQL(", ").join(
                        sql.SQL("{col} = EXCLUDED.{col}").format(col=sql.Identifier(col))
                        for col in update_columns
                    )
                )

                cursor.execute(sql_operation)

        return 0

    def upsert_dataframe_dto(
            self,
            dataframe: pl.DataFrame,
            table_name: str,
            conflict_columns: List[str]
    ):
        start_time = time.time()
        modified_dataframe = dataframe.with_columns(
            pl.col(pl.Struct, pl.Object)
            .map_elements(self._adapt_composite, return_dtype=pl.Object)
        )

        if modified_dataframe.height < 500:
            return_value = self._upsert_small_dataframe_dto_safe(
                modified_dataframe,
                table_name,
                conflict_columns
            )
        else:
            return_value = self._upsert_bulk_dataframe_dto_safe(
                modified_dataframe,
                table_name,
                conflict_columns
            )

        end_time = time.time()
        self.logger.info(f"upserted {dataframe.height} rows into {table_name}, took {end_time - start_time} seconds")

        return return_value
