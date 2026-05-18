from sqlalchemy.orm import Session

from models import sales as models


def save_sale(db: Session, db_note: models.SalesNote) -> models.SalesNote:
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note