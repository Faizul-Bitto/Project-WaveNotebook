import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaTrash, FaSearch, FaEye, FaPlus } from 'react-icons/fa';
import {
  adminGetOrders,
  adminUpdateOrderStatus,
  adminDeleteOrder,
  adminSearchOrders,
} from '../../api/adminServices';

const STATUS_LABELS = {
  pending: 'Pending',
  called: 'Called',
  confirmed: 'Confirmed',
  processing: 'Processing',
  shipped: 'Shipped',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
};

function AdminOrders() {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchType, setSearchType] = useState('phone');
  const [searchValue, setSearchValue] = useState('');

  const loadOrders = async (status = '') => {
    try {
      setLoading(true);
      const params = {};
      if (status) params.status = status;
      const data = await adminGetOrders(params);
      setOrders(data.orders || []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load orders.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await adminGetOrders({});
        if (mounted) setOrders(data.orders || []);
        if (mounted) setError(null);
      } catch (err) {
        if (mounted) setError(err.response?.data?.detail || 'Failed to load orders.');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchData();
    return () => {
      mounted = false;
    };
  }, []);

  const handleStatusChange = (e) => {
    const value = e.target.value;
    setStatusFilter(value);
    loadOrders(value);
  };

  const handleStatusUpdate = async (orderId, newStatus) => {
    try {
      await adminUpdateOrderStatus(orderId, newStatus);
      await loadOrders(statusFilter);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update order status.');
    }
  };

  const handleDelete = async (orderId, orderNumber) => {
    if (window.confirm(`Are you sure you want to delete order ${orderNumber}?`)) {
      try {
        await adminDeleteOrder(orderId);
        await loadOrders(statusFilter);
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to delete order.');
      }
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchValue.trim()) {
      loadOrders(statusFilter);
      return;
    }
    try {
      setLoading(true);
      const data = await adminSearchOrders(searchType, searchValue.trim());
      setOrders(data.orders || []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to search orders.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h2>Orders</h2>
        <div className="header-actions">
          <button className="btn btn-primary" onClick={() => navigate('/admin/orders/new')}>
            <FaPlus /> Create Order
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="admin-filters">
        <select value={statusFilter} onChange={handleStatusChange}>
          <option value="">All Statuses</option>
          {Object.entries(STATUS_LABELS).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>

        <form className="admin-search" onSubmit={handleSearch}>
          <select value={searchType} onChange={(e) => setSearchType(e.target.value)}>
            <option value="phone">Phone</option>
            <option value="name">Name</option>
            <option value="address">Address</option>
          </select>
          <input
            type="text"
            placeholder="Search..."
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
          />
          <button type="submit" className="btn btn-primary">
            <FaSearch />
          </button>
        </form>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="loading">Loading orders...</div>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Order #</th>
                <th>Customer</th>
                <th>Phone</th>
                <th>District</th>
                <th>Total</th>
                <th>Status</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {orders.length === 0 ? (
                <tr>
                  <td colSpan="8" className="table-empty">No orders found</td>
                </tr>
              ) : (
                orders.map((order) => (
                  <tr key={order.id}>
                    <td>{order.order_number}</td>
                    <td>{order.full_name}</td>
                    <td>{order.phone_number}</td>
                    <td>{order.district}</td>
                    <td>৳{parseFloat(order.total_price).toLocaleString()}</td>
                    <td>
                      <select
                        className={`status-select status-${order.status}`}
                        value={order.status}
                        onChange={(e) => handleStatusUpdate(order.id, e.target.value)}
                      >
                        {Object.entries(STATUS_LABELS).map(([value, label]) => (
                          <option key={value} value={value}>{label}</option>
                        ))}
                      </select>
                    </td>
                    <td>{new Date(order.created_at).toLocaleDateString()}</td>
                    <td>
<div className="table-actions">
                      <button
                        className="action-btn action-edit"
                        onClick={() => navigate(`/admin/orders/${order.id}`)}
                        aria-label={`View order ${order.order_number}`}
                      >
                        <FaEye />
                      </button>
                      <button
                        className="action-btn action-delete"
                        onClick={() => handleDelete(order.id, order.order_number)}
                        aria-label={`Delete order ${order.order_number}`}
                      >
                        <FaTrash />
                      </button>
                    </div>
</td>
</tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default AdminOrders;