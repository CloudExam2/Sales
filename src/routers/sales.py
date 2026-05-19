from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from crud import sales as sales_crud
from database import get_db
from models import sales as models
from schemas import sales as sales_schema
from services import get_catalog_base_price, validate_catalog_entities
from sqs_notify import publish_sale_created

router = APIRouter()


@router.get("/", response_model=list[sales_schema.SalesNoteRead])
def list_sales_notes(db: Session = Depends(get_db)):
    return db.query(models.SalesNote).all()


@router.get("/{note_id}", response_model=sales_schema.SalesNoteRead)
def get_sales_note(note_id: int, db: Session = Depends(get_db)):
    note = db.get(models.SalesNote, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Sales note not found")
    return note


@router.post("/", response_model=sales_schema.SalesNoteRead)
async def create_sales_note(note: sales_schema.SalesNoteCreate, db: Session = Depends(get_db)):
    product_ids = [item.product_id for item in note.contents]
    await validate_catalog_entities(note.client_id, product_ids)

    grand_total = 0
    db_contents = []
    for item in note.contents:
        unit_price = await get_catalog_base_price(item.product_id)
        line_total = unit_price * item.quantity
        grand_total += line_total
        db_contents.append(
            models.NoteContent(
                product_id=item.product_id,
                unit_price=unit_price,
                quantity=item.quantity,
                total=line_total,
            )
        )

    db_note = models.SalesNote(
        folio=note.folio,
        client_id=note.client_id,
        fac_address_id=note.fac_address_id,
        send_address_id=note.send_address_id,
        total=grand_total,
        contents=db_contents,
    )

    saved = sales_crud.save_sale(db, db_note)
    publish_sale_created(saved)
    return saved


@router.delete("/{note_id}")
def delete_sales_note(note_id: int, db: Session = Depends(get_db)):
    note = db.get(models.SalesNote, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Sales note not found")
    db.delete(note)
    db.commit()
    return {"ok": True}
