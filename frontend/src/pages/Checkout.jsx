import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FaCheckCircle, FaTruck } from 'react-icons/fa';
import { useCart } from '../context/CartContext';
import { useDirectBuy } from '../context/DirectBuyContext';
import { createOrder, getDistricts } from '../api/services';

function Checkout() {
  const { cart, clearAll } = useCart();
  const { directItem, clearDirectItem } = useDirectBuy();
  const [districts, setDistricts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [orderSuccess, setOrderSuccess] = useState(null);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    full_name: '',
    phone_number: '',
    district: '',
    thana: '',
    note: '',
    address: '',
  });

  useEffect(() => {
    const loadDistricts = async () => {
      try {
        const data = await getDistricts();
        setDistricts(data.districts || []);
      } catch (err) {
        console.error('Failed to load districts:', err);
      }
    };
    loadDistricts();
  }, []);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Validate
    if (!formData.full_name.trim()) {
      setError('Please enter your full name.');
      return;
    }
    if (!formData.phone_number.trim() || formData.phone_number.trim().length < 11) {
      setError('Please enter a valid phone number (11 digits).');
      return;
    }
    if (!formData.district) {
      setError('Please select your district.');
      return;
    }
    if (!formData.thana.trim()) {
      setError('Please enter your thana / upazila.');
      return;
    }
    if (!formData.address.trim()) {
      setError('Please enter your address.');
      return;
    }

    let items;
    if (directItem) {
      items = [{ product_id: directItem.product.id, quantity: directItem.quantity, selected_attributes: directItem.attrsString }];
    } else {
      items = (cart?.items || []).map((item) => ({
        product_id: item.product_id,
        quantity: item.quantity,
        selected_attributes: item.selected_attributes || null,
      }));
    }

    if (items.length === 0) {
      setError(directItem ? 'Product not available.' : 'Your cart is empty.');
      return;
    }

    try {
      setLoading(true);
      const orderData = {
        full_name: formData.full_name,
        phone_number: formData.phone_number,
        district: formData.district,
        thana: formData.thana,
        note: formData.note || null,
        address: formData.address,
        items,
      };
      const result = await createOrder(orderData);
      setOrderSuccess(result.order);
      await clearAll();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to place order. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Order success screen
  if (orderSuccess) {
    return (
      <div className="container order-success">
        <FaCheckCircle className="success-icon" />
        <h1>Order Placed Successfully!</h1>
        <p className="order-number">Order Number: <strong>{orderSuccess.order_number}</strong></p>
        <p>Thank you for your order! We will contact you shortly to confirm.</p>
        <div className="order-summary-box">
          <h3>Order Summary</h3>
          <p><strong>Name:</strong> {orderSuccess.full_name}</p>
          <p><strong>Phone:</strong> {orderSuccess.phone_number}</p>
          <p><strong>District:</strong> {orderSuccess.district}</p>
          <p><strong>Thana:</strong> {orderSuccess.thana}</p>
          <p><strong>Address:</strong> {orderSuccess.address}</p>
          <p><strong>Total:</strong> ৳{parseFloat(orderSuccess.total_price).toLocaleString()}</p>
          <p><strong>Payment:</strong> Cash on Delivery</p>
        </div>
        <Link to="/" className="btn btn-primary">Continue Shopping</Link>
      </div>
    );
  }

  const items = directItem ? [{
    id: 'direct',
    product_name: directItem.product.name,
    slug: directItem.product.slug,
    quantity: directItem.quantity,
    unit_price: directItem.product.base_price,
    subtotal: (parseFloat(directItem.product.base_price) * directItem.quantity).toFixed(2),
  }] : (cart?.items || []);
  const totalPrice = directItem
    ? parseFloat(directItem.product.base_price || 0) * directItem.quantity
    : parseFloat(cart?.total_price || '0');

  if (items.length === 0) {
    return (
      <div className="container empty-state">
        <h2>Your cart is empty</h2>
        <p>Add some products before checking out.</p>
        <Link to="/products" className="btn btn-primary">Browse Products</Link>
      </div>
    );
  }

  return (
    <div className="checkout-page">
      <div className="container">
        <div className="page-header">
          <h1>Checkout</h1>
        </div>

        <div className="checkout-layout">
          {/* Shipping Form */}
          <form className="checkout-form" onSubmit={handleSubmit}>
            <h2>Shipping Information</h2>

            {error && <div className="alert alert-error">{error}</div>}

            <div className="form-group">
              <label htmlFor="full_name">Full Name *</label>
              <input
                type="text"
                id="full_name"
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                placeholder="Enter your full name"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="phone_number">Phone Number *</label>
              <input
                type="tel"
                id="phone_number"
                name="phone_number"
                value={formData.phone_number}
                onChange={handleChange}
                placeholder="01XXXXXXXXX"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="district">District *</label>
              <select
                id="district"
                name="district"
                value={formData.district}
                onChange={handleChange}
                required
              >
                <option value="">Select District</option>
                {districts.map((district) => (
                  <option key={district} value={district}>
                    {district}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="thana">Thana / Upazila *</label>
              <input
                type="text"
                id="thana"
                name="thana"
                value={formData.thana}
                onChange={handleChange}
                placeholder="Enter your thana / upazila"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="address">Full Address *</label>
              <textarea
                id="address"
                name="address"
                value={formData.address}
                onChange={handleChange}
                placeholder="House, Road, Area, Thana"
                rows="3"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="note">Note (optional)</label>
              <textarea
                id="note"
                name="note"
                value={formData.note}
                onChange={handleChange}
                placeholder="Add a short note for the seller (optional)"
                rows="2"
              />
            </div>

            <div className="payment-method">
              <FaTruck className="payment-icon" />
              <div>
                <h4>Cash on Delivery</h4>
                <p>Pay in cash when you receive your order.</p>
              </div>
            </div>

            <button type="submit" className="btn btn-primary btn-lg" disabled={loading}>
              {loading ? 'Placing Order...' : 'Place Order'}
            </button>
          </form>

          {/* Order Summary */}
          <div className="checkout-summary">
            <h2>Order Summary</h2>
            {items.map((item) => (
              <div className="checkout-item" key={item.id}>
                <div className="checkout-item-info">
                  <span className="checkout-item-name">{item.product_name}</span>
                  {item.selected_attributes_display && (
                    <span className="checkout-item-qty">{item.selected_attributes_display}</span>
                  )}
                  <span className="checkout-item-qty">Qty: {item.quantity}</span>
                </div>
                <span className="checkout-item-price">
                  ৳{parseFloat(item.subtotal).toLocaleString()}
                </span>
              </div>
            ))}
            <div className="checkout-total">
              <span>Total</span>
              <span>৳{totalPrice.toLocaleString()}</span>
            </div>
            <p className="checkout-note">
              * Delivery charge will be confirmed by phone.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Checkout;