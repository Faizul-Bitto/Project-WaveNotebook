import { useState } from 'react';
import { FaSearch, FaBoxOpen } from 'react-icons/fa';
import { trackOrder } from '../api/services';

const STATUS_LABELS = {
  pending: 'Pending',
  called: 'Called',
  confirmed: 'Confirmed',
  processing: 'Processing',
  shipped: 'Shipped',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
};

function TrackOrder() {
  const [phone, setPhone] = useState('');
  const [orders, setOrders] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searched, setSearched] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!phone.trim() || phone.trim().length < 11) {
      setError('Please enter a valid phone number (11 digits).');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await trackOrder(phone.trim());
      setOrders(data.orders);
      setSearched(true);
    } catch (err) {
      setOrders(null);
      setSearched(true);
      setError(err.response?.data?.detail || 'Failed to track order.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="track-order-page">
      <div className="container">
        <div className="page-header">
          <h1>Track Your Order</h1>
          <p>Enter your phone number to see all your orders.</p>
        </div>

        <form className="track-form" onSubmit={handleSubmit}>
          <input
            type="tel"
            placeholder="Enter your phone number (01XXXXXXXXX)"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <button type="submit" className="btn btn-primary" disabled={loading}>
            <FaSearch /> {loading ? 'Searching...' : 'Track Order'}
          </button>
        </form>

        {error && <div className="alert alert-error">{error}</div>}

        {orders && orders.length > 0 && (
          <div className="orders-list">
            {orders.map((order) => (
              <div className="order-card" key={order.id}>
                <div className="order-card-header">
                  <div>
                    <h3>Order #{order.order_number}</h3>
                    <p className="order-date">
                      {new Date(order.created_at).toLocaleDateString('en-GB', {
                        day: 'numeric',
                        month: 'long',
                        year: 'numeric',
                      })}
                    </p>
                  </div>
                  <span className={`order-status status-${order.status}`}>
                    {STATUS_LABELS[order.status] || order.status}
                  </span>
                </div>

                <div className="order-card-body">
                  <div className="order-info-row">
                    <span>Name:</span>
                    <strong>{order.full_name}</strong>
                  </div>
                  <div className="order-info-row">
                    <span>District:</span>
                    <strong>{order.district}</strong>
                  </div>
                  <div className="order-info-row">
                    <span>Thana:</span>
                    <strong>{order.thana}</strong>
                  </div>
                  {order.note && (
                    <div className="order-info-row">
                      <span>Note:</span>
                      <strong>{order.note}</strong>
                    </div>
                  )}
                  <div className="order-info-row">
                    <span>Address:</span>
                    <strong>{order.address}</strong>
                  </div>
                  <div className="order-info-row">
                    <span>Items:</span>
                    <strong>{order.items.length}</strong>
                  </div>
                  <div className="order-info-row">
                    <span>Total:</span>
                    <strong>৳{parseFloat(order.total_price).toLocaleString()}</strong>
                  </div>
                </div>

                <div className="order-card-items">
                  {order.items.map((item) => (
                    <div className="order-item" key={item.id}>
                      <span>{item.product_name || `Product #${item.product_id}`}</span>
                      {item.selected_attributes_display && (
                        <span className="order-item-attributes">{item.selected_attributes_display}</span>
                      )}
                      <span>Qty: {item.quantity}</span>
                      <span>৳{parseFloat(item.price_at_purchase).toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {searched && !loading && !error && (!orders || orders.length === 0) && (
          <div className="empty-state">
            <FaBoxOpen className="empty-icon" />
            <h3>No orders found</h3>
            <p>No orders were found for this phone number.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default TrackOrder;