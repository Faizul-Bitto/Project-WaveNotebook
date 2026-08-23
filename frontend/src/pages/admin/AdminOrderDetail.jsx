import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FaArrowLeft, FaBoxOpen, FaUser, FaPhone, FaMapMarkerAlt, FaClipboardList, FaTrash, FaEdit, FaCopy, FaFileInvoice } from 'react-icons/fa';
import { adminGetOrder, adminDeleteOrder, adminGetOrderAdjustments, adminCreateOrderAdjustment, adminDeleteOrderAdjustment, adminDownloadInvoice } from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';
import Modal from '../../components/Modal';

// Build a BOGO label for an item that has free/discounted bonus units.
// For 100% free BOGO: shows "N FREE". For partial BOGO: returns null
// (discount is shown in the summary, not as an extra item badge).
function getBogoInfo(item) {
  const bonus = item.bonus_quantity || 0;
  if (!bonus) return null;
  const pct = item.bogo_get_discount_percent;
  const isFullFree = pct != null && pct >= 100;
  if (!isFullFree) return null;
  const label = `${bonus} FREE`;
  return { bonus, label, isFullFree };
}

function AdminOrderDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [adjustments, setAdjustments] = useState([]);
  const [adjLoading, setAdjLoading] = useState(false);
  const [adjForm, setAdjForm] = useState({ type: 'manual_discount', amount: '', reason: '' });
  const [invoiceLoading, setInvoiceLoading] = useState(false);

  useEffect(() => {
    adminGetOrder(id)
      .then((data) => setOrder(data.order))
      .catch((err) => addToast(err.response?.data?.detail || 'Failed to load order.', 'error'))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!order) return;
    setAdjLoading(true);
    adminGetOrderAdjustments(order.id)
      .then((data) => setAdjustments(data.adjustments || []))
      .catch((err) => addToast(err.response?.data?.detail || 'Failed to load adjustments.', 'error'))
      .finally(() => setAdjLoading(false));
  }, [order]);

  const refreshOrderAndAdjustments = async () => {
    if (!order) return;
    try {
      const [orderData, adjData] = await Promise.all([
        adminGetOrder(id),
        adminGetOrderAdjustments(order.id),
      ]);
      setOrder(orderData.order);
      setAdjustments(adjData.adjustments || []);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to refresh.', 'error');
    }
  };

  const handleCreateAdjustment = async (e) => {
    e.preventDefault();
    if (!adjForm.amount || parseFloat(adjForm.amount) <= 0) {
      addToast('Please enter a valid amount.', 'error');
      return;
    }
    setAdjLoading(true);
    try {
      await adminCreateOrderAdjustment(order.id, {
        adjustment_type: adjForm.type,
        amount: parseFloat(adjForm.amount),
        reason: adjForm.reason || null,
      });
      addToast('Adjustment applied successfully!', 'success');
      setAdjForm({ type: 'manual_discount', amount: '', reason: '' });
      await refreshOrderAndAdjustments();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to apply adjustment.', 'error');
    } finally {
      setAdjLoading(false);
    }
  };

  const handleDeleteAdjustment = async (adjustmentId) => {
    if (!confirm('Are you sure you want to reverse this adjustment? This will update the order total.')) return;
    setAdjLoading(true);
    try {
      await adminDeleteOrderAdjustment(order.id, adjustmentId);
      addToast('Adjustment reversed successfully!', 'success');
      await refreshOrderAndAdjustments();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to reverse adjustment.', 'error');
    } finally {
      setAdjLoading(false);
    }
  };

  const handleDelete = async () => {
    setShowDeleteModal(false);
    try {
      await adminDeleteOrder(id);
      addToast('Order deleted successfully!', 'success');
      navigate('/admin/orders');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to delete.', 'error');
    }
  };

  const handleDownloadInvoice = async () => {
    setInvoiceLoading(true);
    try {
      const response = await adminDownloadInvoice(id);
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `invoice-${order.order_number}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      addToast('Invoice downloaded successfully!', 'success');
    } catch (err) {
      addToast('Failed to download invoice. Please try again.', 'error');
    } finally {
      setInvoiceLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (!order) return <div className="alert alert-error">Order not found</div>;

  return (
    <div className="admin-page order-detail-page">
      <div className="admin-page-header">
        <h2>Order #{order.order_number}</h2>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={() => navigate('/admin/orders')}><FaArrowLeft /> Back</button>
          <button
            className="btn btn-primary"
            onClick={handleDownloadInvoice}
            disabled={invoiceLoading}
            title="Download invoice as PDF"
          >
            <FaFileInvoice /> {invoiceLoading ? 'Generating...' : 'Invoice'}
          </button>
          <button className="btn btn-primary" onClick={() => navigate(`/admin/orders/${order.id}/edit`)}><FaEdit /> Edit</button>
          <button className="btn btn-danger" onClick={handleDelete}><FaTrash /> Delete</button>
        </div>
      </div>
      <div className="order-detail-card">
        <h3><FaClipboardList /> Order Summary</h3>
        <div className="order-detail-grid">
          <div className="detail-item"><span className="detail-label">Order Number</span><span className="detail-value">{order.order_number} <button type="button" className="btn btn-copy btn-sm" onClick={() => { navigator.clipboard.writeText(order.order_number ); addToast('Order number copied!', 'success'); }} title="Copy order number"><FaCopy /></button></span></div>
          <div className="detail-item"><span className="detail-label">Date</span><span className="detail-value">{new Date(order.created_at).toLocaleString()}</span></div>
          { order.simple_bogo !== true && <div className="detail-item"><span className="detail-label">Subtotal</span><span className="detail-value">৳{order.subtotal_before_discount ? parseFloat(order.subtotal_before_discount).toLocaleString() : '0'}</span></div> }
          { order.simple_bogo !== true && order.total_discount && parseFloat(order.total_discount) > 0 && (
            <div className="detail-item discount-summary-row">
              <span className="detail-label">Discount</span>
              <span className="discount-value">-৳{parseFloat(order.total_discount).toLocaleString()}</span>
            </div>
          )}
          {order.free_shipping && (
            <div className="detail-item">
              <span className="detail-label">Shipping</span>
              <span className="discount-value">🚚 Free Shipping</span>
            </div>
          )}
          { order.bogo_free_note && (
            <div className="detail-item">
              <span className="detail-label">Offer</span>
              <span className="detail-value" style={{ color: 'var(--primary)' }}>{order.bogo_free_note}</span>
            </div>
          )}
          <div className="detail-item"><span className="detail-label">Total</span><span className="detail-value total-price">৳{parseFloat(order.total_price).toLocaleString()}</span></div>
        </div>
        { order.discount_breakdown && order.discount_breakdown.length > 0 && (
          <div className="discount-breakdown-detail">
            <h4>Discount Breakdown</h4>
            {order.discount_breakdown.filter((entry) => parseFloat(entry.amount || 0) > 0 || entry.type === 'bogo').map((entry, idx) => {
              const isBogoFree = entry.type === 'bogo' && parseFloat(entry.get_discount_percent || entry['get_discount_percent'] || 0) >= 100;
              return (
                <div className="discount-summary-row" key={idx}>
                  <span className="discount-label">
                    {entry.name || (entry.type === 'price_discount' ? 'Discount' : entry.type)}
                  </span>
                  <span className="discount-value">
                    {isBogoFree ? 'FREE' : `-৳${parseFloat(entry.amount || 0).toLocaleString()}`}
                  </span>
                </div>
              );
            })}
          </div>
        )}
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
                  <td>
                    <div className="product-cell">
                      <span className="product-name">{item.product_name || `Product #${item.product_id || '(deleted)'}`}</span>
                      {item.product_code && <span className="product-code">Code: {item.product_code}</span>}
                      {item.product_id === null && <span className="badge badge-warning">Deleted</span>}
                    </div>
                  </td>
                  <td>{item.selected_attributes_display || '—'}</td>
                  <td>
                    <div className="qty-breakdown">
                      {getBogoInfo(item) ? (
                        <span className="qty-total">
                          {item.quantity + getBogoInfo(item).bonus} = {item.quantity} + {getBogoInfo(item).label} (BOGO)
                        </span>
                      ) : (
                        <span>{item.quantity}</span>
                      )}
                    </div>
                  </td>
                  <td>৳{parseFloat(item.price_at_purchase).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="order-detail-card">
        <h3><FaClipboardList /> Order Adjustments</h3>
        {adjustments.length > 0 && (
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Amount</th>
                  <th>Before</th>
                  <th>After</th>
                  <th>Reason</th>
                  <th>Admin</th>
                  <th>Date</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {adjustments.map((adj) => (
                  <tr key={adj.id}>
                    <td>
                      <span className={`badge ${adj.adjustment_type === 'manual_discount' ? 'badge-success' : adj.adjustment_type === 'manual_charge' ? 'badge-danger' : 'badge-warning'}`}>
                        {adj.adjustment_type}
                      </span>
                    </td>
                    <td className={adj.adjustment_type === 'manual_discount' ? 'discount-amount' : 'charge-amount'}>
                      {adj.adjustment_type === 'manual_discount' ? '-' : '+'}
                      ৳{parseFloat(adj.amount).toLocaleString()}
                    </td>
                    <td>৳{parseFloat(adj.before_total).toLocaleString()}</td>
                    <td>৳{parseFloat(adj.after_total).toLocaleString()}</td>
                    <td>{adj.reason || '—'}</td>
                    <td>{adj.admin_name || `Admin #${adj.admin_user_id}`}</td>
                    <td>{new Date(adj.created_at).toLocaleString()}</td>
                    <td>
                      <button className="btn btn-danger btn-sm" onClick={() => handleDeleteAdjustment(adj.id)} disabled={adjLoading}>
                        Reverse
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Add Adjustment Form */}
        <div className="adjustment-form">
          <h4>Apply Manual Adjustment</h4>
          <form onSubmit={handleCreateAdjustment}>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="adj-type">Type</label>
                <select id="adj-type" value={adjForm.type} onChange={(e) => setAdjForm({ ...adjForm, type: e.target.value })}>
                  <option value="manual_discount">Discount (reduce total)</option>
                  <option value="manual_charge">Charge (increase total)</option>
                  <option value="rounding">Rounding</option>
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="adj-amount">Amount (৳)</label>
                <input id="adj-amount" type="number" step="0.01" min="0" value={adjForm.amount} onChange={(e) => setAdjForm({ ...adjForm, amount: e.target.value })} required />
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="adj-reason">Reason</label>
              <textarea id="adj-reason" value={adjForm.reason} onChange={(e) => setAdjForm({ ...adjForm, reason: e.target.value })} placeholder="Reason for adjustment..." rows="2"></textarea>
            </div>
            <button type="submit" className="btn btn-primary" disabled={adjLoading}>
              {adjLoading ? 'Applying...' : 'Apply Adjustment'}
            </button>
          </form>
        </div>
      </div>

      <div className="order-detail-card">
        <h3>Payment</h3>
        <div className="payment-info"><p><strong>Method:</strong> Cash on Delivery</p></div>
      </div>

      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={handleDelete}
        title="Delete Order"
        message={`Are you sure you want to delete order ${order?.order_number}?`}
        confirmText="Delete"
        type="danger"
      />
    </div>
  );
}

export default AdminOrderDetail;