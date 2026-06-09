from abc import ABC, abstractmethod
from typing import List, Self, Dict

import polars as pl


class APIModelInterface(ABC):
    @classmethod
    @abstractmethod
    def to_dataframe(cls, records: List[Self]) -> pl.DataFrame: ...

    @classmethod
    @abstractmethod
    def from_json(cls, *args, **kwargs) -> Self | List[Self]: ...

    @classmethod
    @abstractmethod
    def get_keys(cls) -> List[str]: ...
