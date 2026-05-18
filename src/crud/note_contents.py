from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from models import sales as models


def _line_total(unit_price: Decimal, quantity: int) -> Decimal:
    return Decimal(str(unit_price)) * quantity


def recalculate_note_total(db: Session, note_id: int) -> None:
    note = db.get(models.SalesNote, note_id)
    if not note:
        return
    lines = db.query(models.NoteContent).filter(models.NoteContent.note_id == note_id).all()
    note.total = sum((line.total for line in lines), Decimal("0"))
    db.commit()
    db.refresh(note)


def list_contents(db: Session) -> list[models.NoteContent]:
    return db.query(models.NoteContent).all()


def get_content(db: Session, content_id: int) -> Optional[models.NoteContent]:
    return db.get(models.NoteContent, content_id)


def create_content(db: Session, data: dict) -> models.NoteContent:
    unit_price = data["unit_price"]
    quantity = data["quantity"]
    obj = models.NoteContent(
        note_id=data["note_id"],
        product_id=data["product_id"],
        unit_price=unit_price,
        quantity=quantity,
        total=_line_total(unit_price, quantity),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    recalculate_note_total(db, obj.note_id)
    return obj


def update_content(db: Session, content_id: int, data: dict) -> Optional[models.NoteContent]:
    obj = get_content(db, content_id)
    if not obj:
        return None

    for field, value in data.items():
        setattr(obj, field, value)

    if "unit_price" in data or "quantity" in data:
        obj.total = _line_total(obj.unit_price, obj.quantity)

    db.commit()
    db.refresh(obj)
    recalculate_note_total(db, obj.note_id)
    return obj


def delete_content(db: Session, content_id: int) -> bool:
    obj = get_content(db, content_id)
    if not obj:
        return False
    note_id = obj.note_id
    db.delete(obj)
    db.commit()
    recalculate_note_total(db, note_id)
    return True
