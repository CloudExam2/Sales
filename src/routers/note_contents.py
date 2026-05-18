from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from crud import note_contents as content_crud
from database import get_db
from models import sales as models
from schemas import sales as sales_schema
from services import validate_catalog_entities

router = APIRouter()


def _get_note_or_404(db: Session, note_id: int) -> models.SalesNote:
    note = db.get(models.SalesNote, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Sales note not found")
    return note


@router.get("/", response_model=list[sales_schema.NoteContentRead])
def list_note_contents(db: Session = Depends(get_db)):
    return content_crud.list_contents(db)


@router.post("/", response_model=sales_schema.NoteContentRead)
async def create_note_content(
    body: sales_schema.NoteContentCreate,
    db: Session = Depends(get_db),
):
    note = _get_note_or_404(db, body.note_id)
    await validate_catalog_entities(note.client_id, [body.product_id])
    return content_crud.create_content(db, body.model_dump())


@router.get("/{content_id}", response_model=sales_schema.NoteContentRead)
def get_note_content(content_id: int, db: Session = Depends(get_db)):
    obj = content_crud.get_content(db, content_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Note content not found")
    return obj


@router.put("/{content_id}", response_model=sales_schema.NoteContentRead)
async def update_note_content(
    content_id: int,
    body: sales_schema.NoteContentUpdate,
    db: Session = Depends(get_db),
):
    obj = content_crud.get_content(db, content_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Note content not found")

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        return obj

    note = _get_note_or_404(db, obj.note_id)
    product_id = update_data.get("product_id", obj.product_id)
    await validate_catalog_entities(note.client_id, [product_id])

    updated = content_crud.update_content(db, content_id, update_data)
    return updated


@router.delete("/{content_id}")
def delete_note_content(content_id: int, db: Session = Depends(get_db)):
    if not content_crud.delete_content(db, content_id):
        raise HTTPException(status_code=404, detail="Note content not found")
    return {"ok": True}
