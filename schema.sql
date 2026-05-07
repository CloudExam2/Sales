DROP TABLE IF EXISTS note_contents;
DROP TABLE IF EXISTS sales_notes;

CREATE TABLE sales_notes (
    id SERIAL PRIMARY KEY,
    folio VARCHAR(50) NOT NULL UNIQUE,
    client_id INTEGER NOT NULL,
    fac_address_id INTEGER NOT NULL,
    send_address_id INTEGER NOT NULL,
    total NUMERIC(10,2) DEFAULT 0.00
);

CREATE TABLE note_contents (
    id SERIAL PRIMARY KEY,
    note_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    unit_price NUMERIC(10,2) NOT NULL,
    quantity INTEGER NOT NULL,
    total NUMERIC(10,2) NOT NULL,
    CONSTRAINT fk_sales_note FOREIGN KEY (note_id) REFERENCES sales_notes(id) ON DELETE CASCADE
);