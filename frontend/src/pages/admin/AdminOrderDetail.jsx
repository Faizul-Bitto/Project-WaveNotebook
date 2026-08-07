import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FaArrowLeft, FaBoxOpen, FaUser, FaPhone, FaMapMarkerAlt, FaClipboardList, FaTrash, FaEdit } from 'react-icons/fa';
import { adminGetOrder, adminDeleteOrder } from '../../api/adminServices';

function AdminOrderDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    adminGetOrder(id)
      .then((data) => setOrder(data.order))
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load order.'))
      .finally(() => setLoading(false));
  }, [id]);

  const handleDelete = async () => {
    if (window.confirm(`Delete order ${order.order_number}?`)) {
      try { await adminDeleteOrder(id); navigate('/admin/orders'); }
      catch (err) { alert(err.response?.data?.detail || 'Failed to delete.'); }
    }
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (error || !order) return <div className="alert alert-error">{error || 'Not found'}</div>;

  return (
    <div className="admin-page order-detail-page">
      <div className="admin-page-header">
        <h2>Order #{order.order_number}</h2>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={() => navigate('/admin/orders')}><FaArrowLeft /> Back</button>
          <button className="btn btn-primary" onClick={() => navigate(`/admin/orders/${order.id}/edit`)}><FaEdit /> Edit</button>
          <button className="btn btn-danger" onClick={handleDelete}><FaTrash /> Delete</button>
        </div>
      </div>
      <div className="order-detail-card">
        <h3><FaClipboardList /> Order Summary</h3>
        <div className="order-detail-grid">
          <div className="detail-item"><span className="detail-label">Order Number</span><span className="detail-value">{order.order_number}</span></div>
          <div className="detail-item"><span className="detail-label">Date</span><span className="detail-value">{new Date(order.created_at).toLocaleString()}</span></div>
          <div className="detail-item"><span className="detail-label">Total</span><span className="detail-value total-price">৳{parseFloat(order.total_price).toLocaleString()}</span></div>
        </div>
      </div>
      <div className="order-detail-card">
        <h3><FaUser /> Customer Information</h3>
        <div className="order-detail-grid">
          <div className="detail-item"><span className="detail-label">Name</span><span className="detail-value">{order.full_name}</span></div>
          <div className="detail-item"><span className="detail-label">Phone</span><span className="detail-value"><FaPhone /> {order.phone_number}</span></div>
          <div className="detail-item"><span className="detail-label">District</span><span className="detail-value"><FaMapMarkerAlt /> {order.district}</span></div>
          <div className="detail-item"><span className="detail-label">Thana</span><span className="detail-value"><FaMapMarkerAlt /> {order.thana}</span></div>
        </div>
        <div className="detail-item address-full"><span className="detail-label">Address</span><span className="detail-value">{order.address}</span></div>
        {order.note && <div className="detail-item address-full"><span className="detail-label">Note</span><span className="detail-value">{order.note}</span></div>}
      </div>
      <div className="order-detail-card">
        <h3><FaBoxOpen /> Items ({order.items.length})</h3>
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr><th>#</th><th>Product</th><th>Options</th><th>Qty</th><th>Total</th></tr>
            </thead>
            <tbody>
              {order.items.map((item, i) => (
                <tr key={item.id || i}>
                  <td>{i + 1}</td>
                  <td>{item.product_name || `Product #${item.product_id}`}</td>
                  <td>{item.selected_attributes_display || '—'}</td>
                  <td>{item.quantity}</td>
                  <td>৳{parseFloat(item.price_at_purchase).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="order-detail-card">
        <h3>Payment</h3>
        <div className="payment-info"><p><strong>Method:</strong> Cash on Delivery</p></div>
      </div>
    </div>
  );
}

export default AdminOrderDetail;