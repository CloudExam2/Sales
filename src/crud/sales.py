from sqlalchemy.orm import Session
from Sales.src.models import sales
from schemas import sales as schema

def save_sale(db: Session, sale_data: schema.SalesNoteCreate) -> sales.SalesNote:
    # 1. Create the Database Object
    db_sale = sales.SalesNote(folio=sale_data.folio, total=sale_data.total)
    # 2. Add it to the session
    db.add(db_sale)
    # 3. Save it to the .db file
    db.commit()
    # 4. Refresh to get the generated ID
    db.refresh(db_sale)
    return db_sale