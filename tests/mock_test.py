import os

import polars as pl
import pytest

from utils.postgres.postgres_connection import PostgresConnection


class NumberDto:
    def __init__(self, number: int):
        self.number = number

    def to_tuple(self) -> tuple:
        return (self.number,)


@pytest.fixture
def connection_wrapper():
    url = os.environ.get("INTEGRATION_DATABASE_URL")
    assert url is not None

    with PostgresConnection(url) as connection:
        yield connection


def test_upsert_dataframe_dto_writes_composite_rows(connection_wrapper):
    test_df = pl.DataFrame(
        {
            "id": [num for num in range(1000)],
            "dto_test": [NumberDto(num) for num in range(1000, 2000)],
        }
    )

    with connection_wrapper.connection.cursor() as cursor:
        cursor.execute("TRUNCATE test_table")

    connection_wrapper.connection.commit()

    connection_wrapper.upsert_dataframe_dto(
        test_df,
        "test.test_table",
        ["id"]
    )

    with connection_wrapper.connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM test_table")
        row_count = cursor.fetchone()[0]

        cursor.execute("SELECT (dto_test).number FROM test_table WHERE id = 0")
        first_dto_number = cursor.fetchone()[0]

    assert row_count == 1000
    assert first_dto_number == 1000


def test_upsert_dataframe_dto_writes_composite_rows_small(connection_wrapper):
    test_df = pl.DataFrame(
        {
            "id": [num for num in range(10)],
            "dto_test": [NumberDto(num) for num in range(1000, 1010)],
        }
    )

    with connection_wrapper.connection.cursor() as cursor:
        cursor.execute("TRUNCATE test_table")

    connection_wrapper.connection.commit()

    connection_wrapper.upsert_dataframe_dto(
        test_df,
        "test_table",
        ["id"]
    )

    with connection_wrapper.connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM test_table")
        row_count = cursor.fetchone()[0]

        cursor.execute("SELECT (dto_test).number FROM test_table WHERE id = 0")
        first_dto_number = cursor.fetchone()[0]

    assert row_count == 10
    assert first_dto_number == 1000
