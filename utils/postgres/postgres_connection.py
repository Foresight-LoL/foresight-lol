from typing import List

import psycopg
import polars as pl
from psycopg import sql

class PostgresConnection:
    def __init__(self, url: str):
        print("opening connection")
        self.connection: psycopg.Connection = psycopg.connect(url)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self):
        print("closing connection")
        if self.connection and not self.connection.closed:
            self.connection.close()

    @classmethod
    def dict_to_tuple(cls, dictionary: dict) -> tuple:
        return tuple(
            cls.dict_to_tuple(value) if isinstance(value, dict) else value
            for value in dictionary.values()
        )

    def upsert_dataframe_dto_safe(
            self,
            dataframe: pl.DataFrame,
            table_name: str,
            conflict_columns: List[str]
    ):
        if dataframe.is_empty():
            return 1

        columns = dataframe.columns
        update_columns = [col for col in columns if col not in conflict_columns]

        if len(update_columns) == 0:
            return 1

        sql_operation = sql.SQL(
        """
          INSERT INTO {table_name} ({column_list_str})
          VALUES ({bind_arguments_str})
          ON CONFLICT ({conflict_clause_str})
          DO UPDATE SET {update_clause_str}
        """
        ).format(
            table_name=sql.Identifier(table_name),
            column_list_str = sql.SQL(", ").join(map(sql.Identifier, columns)),
            bind_arguments_str = sql.SQL(", ").join(sql.Placeholder() * len(columns)),
            conflict_clause_str = sql.SQL(", ").join(map(sql.Identifier, conflict_columns)),
            update_clause_str = sql.SQL(", ").join(
                sql.SQL("{col} = EXCLUDED.{col}").format(col=sql.Identifier(col))
                for col in update_columns
            ),
        )

        with self.connection.transaction():
            with self.connection.cursor() as cursor:
                cursor.executemany(
                    sql_operation,
                    dataframe.with_columns(
                        pl.col(pl.Struct).map_elements(
                            self.dict_to_tuple,
                            return_dtype=pl.Object
                        )
                    )
                    .rows()
                )

        return 0