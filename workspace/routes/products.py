from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix='/api/products', tags=['Products'])

class Product(BaseModel):
    id: str
    name: str
    price: float
    stock: int

PRODUCTS_DB = [
    {'id': 'prod_1', 'name': 'Mechanical Keyboard', 'price': 99.99, 'stock': 24},
    {'id': 'prod_2', 'name': 'UltraWide Monitor', 'price': 349.50, 'stock': 8},
    {'id': 'prod_3', 'name': 'Ergonomic Mouse', 'price': 59.00, 'stock': 42},
]

@router.get('', response_model=List[Product])
def list_products(min_price: Optional[float] = None, max_price: Optional[float] = None):
    res = PRODUCTS_DB
    if min_price is not None:
        res = [p for p in res if p['price'] >= min_price]
    if max_price is not None:
        res = [p for p in res if p['price'] <= max_price]
    return res

@router.post('/{product_id}/decrement')
def decrement_stock(product_id: str, count: int = 1):
    p = next((x for x in PRODUCTS_DB if x['id'] == product_id), None)
    if not p:
        raise HTTPException(status_code=404, detail='Product not found')
    if p['stock'] < count:
        raise HTTPException(status_code=400, detail='Insufficient stock')
    p['stock'] -= count
    return {'success': True, 'remaining_stock': p['stock']}
