import { useState } from 'react';
import { FaSearch, FaBoxOpen, FaPhoneAlt, FaHashtag } from 'react-icons/fa';
import { trackOrder, trackOrderByNumber } from '../api/services';
import PhoneInput from '../components/PhoneInput';
import { useToast } from '../context/ToastContext';

const STATUS_LABELS = {
  pending: 'Pending',
  called: 'Called',
  confirmed: 'Confirmed',
  processing: 'Processing',
  shipped: 'Shipped',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
  returned: 'Returned',
};

function TrackOrder() {
  const { addToast } = useToast();
  const [phone, setPhone] = useState('');
  const [orderNumber, setOrderNumber] = useState('');
  const [searchType, setSearchType] = useState('phone');
  const [orders, setOrders] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (searchType === 'order_number') {
      const trimmed = orderNumber.trim().toUpperCase();
      if (!trimmed) {
        addToast('Please enter an order number.', 'error');
        return;
      }
      try {
        setLoading(true);
        const data = await trackOrderByNumber(trimmed);
        setOrders([data.order]);
        setSearched(true);
      } catch (err) {
        setOrders(null);
        setSearched(true);
        addToast(err.response?.data?.detail || 'Order not found.', 'error');
      } finally {
        setLoading(false);
      }
      return;
    }

    if (!phone.trim() || phone.trim().length < 8) {
      addToast('Please enter a valid phone number.', 'error');
      return;
    }

    try {
      setLoading(true);
      const data = await trackOrder(phone.trim());
      setOrders(data.orders);
      setSearched(true);
    } catch (err) {
      setOrders(null);
      setSearched(true);
      addToast(err.response?.data?.detail || 'Failed to track order.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSearchTypeChange = (type) => {
    setSearchType(type);
    setOrders(null);
    setSearched(false);
    setPhone('');
    setOrderNumber('');
  };

  return (
    <div className="track-order-page">
      <div className="container">
        <div className="page-header">
          <h1>Track Your Order</h1>
          <p>Enter your phone number or order number to see your order details.</p>
        </div>

        <div className="track-search-type">
          <button
            className={`track-type-btn ${searchType === 'phone' ? 'active' : ''}`}
            onClick={() => handleSearchTypeChange('phone')}
          >
            <FaPhoneAlt /> By Phone
          </button>
          <button
            className={`track-type-btn ${searchType === 'order_number' ? 'active' : ''}`}
            onClick={() => handleSearchTypeChange('order_number')}
          >
            <FaHashtag /> By Order Number
          </button>
        </div>

        <form className="track-form" onSubmit={handleSubmit}>
          {searchType === 'phone' ? (
            <div className="track-phone-wrap">
              <PhoneInput
                name="phone"
                value={phone}
                onChange={(name, val) => setPhone(val)}
                placeholder="XXXXXXXXXXX"
              />
            </div>
          ) : (
            <div className="track-order-number-wrap">
              <input
                type="text"
                className="form-input"
                placeholder="ORD-20260809-7C0D2"
                value={orderNumber}
                onChange={(e) => setOrderNumber(e.target.value)}
              />
            </div>
          )}
          <button type="submit" className="btn btn-primary" disabled={loading}>
            <FaSearch /> {loading ? 'Searching...' : 'Track Order'}
          </button>
        </form>

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
                    <span>Phone:</span>
                    <strong>{order.phone_number || phone}</strong>
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
                    { order.simple_bogo !== true && (
                    <div className="order-info-row">
                      <span>Subtotal:</span>
                      <strong>৳{order.subtotal_before_discount ? parseFloat(order.subtotal_before_discount).toLocaleString() : parseFloat(order.total_price).toLocaleString()}</strong>
                    </div>
                    )}
                     { order.discount_breakdown && order.discount_breakdown.length > 0 && order.discount_breakdown
                       .filter((entry) => parseFloat(entry.amount || 0) > 0 || entry.type === 'bogo')
                       .map((entry, idx) => {
                         const isBogoFree = entry.type === 'bogo' && parseFloat(entry.get_discount_percent || entry['get_discount_percent'] || 0) >= 100;
                         return (
                           <div className="order-info-row" key={idx}>
                             <span>
                               {entry.name || (entry.type === 'price_discount' ? 'Discount' : entry.type)}
                             </span>
                             <strong className="discount-amount">
                               {isBogoFree ? 'FREE' : `-৳${parseFloat(entry.amount || 0).toLocaleString()}`}
                             </strong>
                           </div>
                         );
                       })}
                    {order.free_shipping && (
                      <div className="order-info-row">
                        <span>Shipping:</span>
                        <strong className="free-shipping-text">🚚 Free</strong>
                      </div>
                    )}
                    { order.simple_bogo !== true && order.total_discount && parseFloat(order.total_discount) > 0 && (
                      <div className="order-info-row">
                        <span>Total Discount:</span>
                        <strong className="discount-amount">-৳{parseFloat(order.total_discount).toLocaleString()}</strong>
                      </div>
                    )}
                     { order.bogo_free_note && (
                       <div className="order-info-row">
                         <span>{order.bogo_free_note}</span>
                       </div>
                     )}
                   <div className="order-info-row">
                     <span>Total:</span>
                     <strong>৳{parseFloat(order.total_price).toLocaleString()}</strong>
                   </div>
                 </div>

                 <div className="order-card-items">
                   {order.items.map((item) => (
                     <div className="order-item" key={item.id}>
                       <span>
                         {item.product_name || `Product #${item.product_id || '(deleted)'}`}
                         {item.product_code && <small className="order-item-code"> ({item.product_code})</small>}
                       </span>
                       {item.selected_attributes_display && (
                         <span className="order-item-attributes">{item.selected_attributes_display}</span>
                       )}
                        <span>
                          Qty: {item.quantity}
                          {item.bonus_quantity > 0 && (item.bogo_get_discount_percent == null || item.bogo_get_discount_percent >= 100) && (
                            <span className="order-item-bogo"> + {item.bonus_quantity} FREE (BOGO)</span>
                          )}
                        </span>
                       <span>৳{parseFloat(item.price_at_purchase).toLocaleString()}</span>
                     </div>
                   ))}
                 </div>
              </div>
            ))}
          </div>
        )}

        {searched && !loading && (!orders || orders.length === 0) && (
          <div className="empty-state">
            <FaBoxOpen className="empty-icon" />
            <h3>No orders found</h3>
            <p>No orders were found. Please check your search criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default TrackOrder;