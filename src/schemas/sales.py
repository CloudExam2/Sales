from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class NoteContentBase(BaseModel):
    product_id: int
    unit_price: Decimal
    quantity: int


class NoteContentLineCreate(NoteContentBase):
    """Line item embedded in POST /sales/ (note_id is set by the parent note)."""

    pass


class NoteContentCreate(NoteContentBase):
    """Standalone POST /note-contents/."""

    note_id: int


class NoteContentUpdate(BaseModel):
    product_id: Optional[int] = None
    unit_price: Optional[Decimal] = None
    quantity: Optional[int] = None


class NoteContentRead(NoteContentBase):
    id: int
    note_id: int
    total: Decimal
    model_config = ConfigDict(from_attributes=True)


class SalesNoteBase(BaseModel):
    folio: str
    client_id: int
    fac_address_id: int
    send_address_id: int


class SalesNoteCreate(SalesNoteBase):
    contents: List[NoteContentLineCreate]


class SalesNoteRead(SalesNoteBase):
    id: int
    total: Decimal
    model_config = ConfigDict(from_attributes=True)
