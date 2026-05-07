from pydantic import BaseModel, ConfigDict
from typing import List
from decimal import Decimal

class NoteContentBase(BaseModel):
    product_id: int
    unit_price: Decimal
    quantity: int

class NoteContentCreate(NoteContentBase):
    pass

class SalesNoteBase(BaseModel):
    folio: str
    client_id: int
    fac_address_id: int
    send_address_id: int

class SalesNoteCreate(SalesNoteBase):
    contents: List[NoteContentCreate]

class SalesNoteRead(SalesNoteBase):
    id: int
    total: Decimal
    model_config = ConfigDict(from_attributes=True)