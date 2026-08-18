import asyncio
from app.core.database import SessionLocal
from app.models.cart_item import CartItem
from app.models.product import Product
from app.apis.cart import get_cart

async def main():
    db = SessionLocal()

    # Simulate cart API call for product 4, qty=10
    cart_session_id = 'test-session-001'
    existing = db.query(CartItem).filter(CartItem.cart_session_id == cart_session_id).first()
    if existing:
        db.query(CartItem).filter(CartItem.cart_session_id == cart_session_id).delete()
        db.commit()

    # Add product 4 to cart with qty=10
    product = db.query(Product).filter(Product.id == 4).first()
    cart_item = CartItem(
        cart_session_id=cart_session_id,
        product_id=4,
        quantity=10,
        selected_attributes=None,
    )
    db.add(cart_item)
    db.commit()

    # Call get_cart
    result = await get_cart(db, cart_session_id)
    print('Cart API response for qty=10:')
    for item in result['items']:
        print(f"  product_id={item['product_id']}, qty={item['quantity']}, discount_amount={item.get('discount_amount')}, discounted_subtotal={item.get('discounted_subtotal')}")
    print(f"  total_price: {result['total_price']}")
    print(f"  total_discount: {result['total_discount']}")
    print(f"  display_subtotal: {result.get('display_subtotal', 'N/A')}")

    db.close()

asyncio.run(main())
