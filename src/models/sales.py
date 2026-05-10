from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from database import Base

class SalesNote(Base):
    __tablename__ = "sales_notes"
    id = Column(Integer, primary_key=True, index=True)
    folio = Column(String(50), unique=True, nullable=False)
    client_id = Column(Integer, nullable=False)
    fac_address_id = Column(Integer, nullable=False)
    send_address_id = Column(Integer, nullable=False)
    total = Column(DECIMAL(10, 2), default=0.00)

    contents = relationship(
        "NoteContent", 
        back_populates="note", 
        cascade="all, delete-orphan"
    )

class NoteContent(Base):
    __tablename__ = "note_contents"
    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("sales_notes.id"))
    product_id = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    total = Column(DECIMAL(10, 2), nullable=False)

    note = relationship("SalesNote", back_populates="contents")