import models
from schemas import sales as sales_schema
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services import validate_catalog_entities

router = APIRouter(prefix="/sales", tags=["sales"])

@router.post("/", response_model=sales_schema.SalesNoteRead)
async def create_sales_note(note: sales_schema.SalesNoteCreate, db: Session = Depends(get_db)):
    # 1. External Validation
    product_ids = [item.product_id for item in note.contents]
    await validate_catalog_entities(note.client_id, product_ids)

    # 2. Calculate Totals
    grand_total = 0
    db_contents = []
    for item in note.contents:
        line_total = item.unit_price * item.quantity
        grand_total += line_total
        db_contents.append(models.NoteContent(**item.model_dump(), total=line_total))

    # 3. Save Sales Note
    db_note = models.SalesNote(
        folio=note.folio,
        client_id=note.client_id,
        fac_address_id=note.fac_address_id,
        send_address_id=note.send_address_id,
        total=grand_total,
        contents=db_contents
    )
    
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note