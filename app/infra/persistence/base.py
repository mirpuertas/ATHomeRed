from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

SCHEMA = "athome"
metadata = MetaData(schema=SCHEMA)


class Base(DeclarativeBase):
    metadata = metadata
