from datetime import date
from typing import Optional

from sqlalchemy import Date, String, create_engine, select
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from nucleo import DB_CONFIG, DB_NAME

engine = create_engine(
    URL.create(
        "mysql+pymysql",
        username=DB_CONFIG["user"],
        password=DB_CONFIG["password"] or None,
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_NAME,
        query={"charset": "utf8mb4"},
    ),
    pool_pre_ping=True,
)


class Base(DeclarativeBase):
    pass


class Estoque(Base):
    __tablename__ = "estoque"

    id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    item: Mapped[str] = mapped_column(String(80))
    quantidade: Mapped[int] = mapped_column(INTEGER(unsigned=True))
    ideal: Mapped[int] = mapped_column(INTEGER(unsigned=True))
    unidade: Mapped[str] = mapped_column(String(20))
    categoria: Mapped[Optional[str]] = mapped_column(String(40))
    fornecedor: Mapped[Optional[str]] = mapped_column(String(80))
    validade: Mapped[Optional[date]] = mapped_column(Date)

    def como_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


def sessao_bd():
    return Session(engine)