from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .bases import NameIntIdEntity


class Productsection(NameIntIdEntity):
    """
    Разделы
    """

    __tablename__ = "productsections"

    def __str__(self) -> str:
        return str(self.name)

    # Каталог и раздел
    catalog_id: Mapped[int | None] = mapped_column(
        comment="Каталог"
    )  # CATALOG_ID : Каталог 25
    xml_id: Mapped[str | None] = mapped_column(
        comment="Внешний код"
    )  # XML_ID : Внешний код
    code: Mapped[str | None] = mapped_column(
        comment="Символьный код"
    )  # CODE : Символьный код
    section_id: Mapped[int | None] = mapped_column(
        ForeignKey("productsections.external_id"), nullable=True
    )  # SECTION_ID

    child_productsections: Mapped[list["Productsection"]] = relationship(
        "Productsection",
        back_populates="parent_productsection",
        foreign_keys="[Productsection.section_id]",
    )
    parent_productsection: Mapped["Productsection | None"] = relationship(
        "Productsection",
        back_populates="child_productsections",
        foreign_keys="[Productsection.section_id]",
        remote_side="[Productsection.external_id]",
    )
