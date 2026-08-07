import { Link } from 'react-router-dom';
import { FaTrash, FaShoppingCart, FaArrowLeft } from 'react-icons/fa';
import { useCart } from '../context/CartContext';

function Cart() {
  const { cart, loading, updateItem, removeItem, clearAll } = useCart();

  const handleQuantityChange = async (itemId, newQuantity) => {
    if (newQuantity < 1) return;
    await updateItem(itemId, newQuantity);
  };

  const handleRemove = async (itemId) => {
    await removeItem(itemId);
  };

  const handleClear = async () => {
    if (window.confirm('Are you sure you want to clear your cart?')) {
      await clearAll();
    }
  };

  if (loading) {
    return <div className="container loading">Loading cart...</div>;
  }

  const items = cart?.items || [];

  if (items.length === 0) {
    return (
      <div className="container empty-state">
        <FaShoppingCart className="empty-icon" />
        <h2>Your cart is empty</h2>
        <p>Browse our products and add items to your cart.</p>
        <Link to="/products" className="btn btn-primary">Start Shopping</Link>
      </div>
    );
  }

  return (
    <div className="cart-page">
      <div className="container">
        <div className="page-header">
          <h1>Shopping Cart</h1>
          <button className="btn btn-outline" onClick={handleClear}>
            Clear Cart
          </button>
        </div>

        <div className="cart-layout">
          {/* Cart Items */}
          <div className="cart-items">
            {items.map((item) => (
              <div className="cart-item" key={item.id}>
                <Link to={`/product/${item.slug}`} className="cart-item-image">
                  <img
                    src={item.image_url || 'https://placehold.co/100x100?text=No+Image'}
                    alt={item.product_name}
                  />
                </Link>

                <div className="cart-item-info">
                  <Link to={`/product/${item.slug}`} className="cart-item-name">
                    {item.product_name}
                  </Link>
                  {item.selected_attributes_display && (
                    <p className="cart-item-attributes">{item.selected_attributes_display}</p>
                  )}
                  <p className="cart-item-price">৳{parseFloat(item.unit_price).toLocaleString()} / unit</p>
                </div>

                <div className="cart-item-quantity">
                  <button
                    onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                    aria-label="Decrease quantity"
                  >
                    -
                  </button>
                  <span>{item.quantity}</span>
                  <button
                    onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                    aria-label="Increase quantity"
                  >
                    +
                  </button>
                </div>

                <div className="cart-item-subtotal">
                  <span>৳{parseFloat(item.subtotal).toLocaleString()}</span>
                </div>

                <button
                  className="cart-item-remove"
                  onClick={() => handleRemove(item.id)}
                  aria-label={`Remove ${item.product_name} from cart`}
                >
                  <FaTrash />
                </button>
              </div>
            ))}
          </div>

          {/* Order Summary */}
          <div className="cart-summary">
            <h2>Order Summary</h2>
            <div className="summary-row">
              <span>Items ({cart?.total_items || 0})</span>
              <span>৳{parseFloat(cart?.total_price || '0').toLocaleString()}</span>
            </div>
            <div className="summary-row">
              <span>Delivery</span>
              <span>Calculated at checkout</span>
            </div>
            <div className="summary-total">
              <span>Total</span>
              <span>৳{parseFloat(cart?.total_price || '0').toLocaleString()}</span>
            </div>
            <Link to="/checkout" className="btn btn-primary btn-lg checkout-btn">
              Proceed to Checkout
            </Link>
            <Link to="/products" className="continue-shopping">
              <FaArrowLeft /> Continue Shopping
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Cart;