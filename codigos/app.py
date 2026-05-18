from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from sqlite3 import connect
import uvicorn
from logging import getLogger, StreamHandler, Formatter, DEBUG, FileHandler
from typing import List, Optional
from pathlib import Path

BASE_DIR = Path(__file__).parent
logger = getLogger(__name__)
logger.setLevel(DEBUG)
handler = StreamHandler()
fileHandler = FileHandler('app.log')
fileHandler.setLevel(DEBUG)
formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(fileHandler)
class Item(BaseModel):
    name: str
    alternative_names: List[str] = []
    description: Optional[str] = None
    price: float = 0.0
    code: str
    unit: str = "kg"
RELOAD = True
connection = connect("items.db", check_same_thread=False)
cursor = connection.cursor()
app = APIRouter()
def initialize_database():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            alternative_names TEXT,
            description TEXT,
            price REAL NOT NULL,
            code TEXT NOT NULL,
            unit TEXT NOT NULL
        )
    ''')
    connection.commit()
@app.get("/")
def read_root():
    return FileResponse(BASE_DIR / 'index.html')
@app.post("/items/")
async def create_item(request: Request):
    # Accept both JSON and form submissions
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
        item = Item(**payload)
    else:
        form = await request.form()
        name = form.get("name")
        code = form.get("code")
        alternative_names = form.get("alternative_names") or ""
        alternative_list = [x.strip() for x in alternative_names.split(",") if x.strip()]
        description = form.get("description") or None
        try:
            price = float(form.get("price") or 0)
        except ValueError:
            price = 0.0
        unit = form.get("unit") or "kg"
        item = Item(name=name, alternative_names=alternative_list, description=description, price=price, code=code, unit=unit)

    logger.info(f"Creating item: {item}")
    cursor.execute('''
        INSERT INTO items (name, alternative_names, description, price, code, unit)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (item.name, ','.join(item.alternative_names), item.description, item.price, item.code, item.unit))
    connection.commit()
    return {"message": "Item created successfully"}

@app.get("/items/")
def read_items():
    cursor.execute('SELECT * FROM items')
    items = cursor.fetchall()
    return {"items": items}
@app.get("/items/{item_id}")
def read_item(item_id: int):
    cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
    item = cursor.fetchone()
    if item:
        return {"item": item}
    else:
        return {"message": "Item not found"}
@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
    connection.commit()
    return {"message": "Item deleted successfully"}
@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    cursor.execute('''
        UPDATE items
        SET name = ?, alternative_names = ?, description = ?, price = ?, code = ?, unit = ?
        WHERE id = ?
    ''', (item.name, ','.join(item.alternative_names), item.description, item.price, item.code, item.unit, item_id))
    connection.commit()
    return {"message": "Item updated successfully"}
@app.post("/items/search/")
def search_items(query: str):
    cursor.execute('''
        SELECT * FROM items
        WHERE name LIKE ? OR alternative_names LIKE ? OR description LIKE ? OR code LIKE ? OR unit LIKE ?
    ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
    items = cursor.fetchall()
    return {"items": items}
if __name__ == "__main__":
    initialize_database()
    uvicorn.run("app:app", host="0.0.0.0", port=80, reload=RELOAD)
def initialize_router():
    initialize_database()
    return app