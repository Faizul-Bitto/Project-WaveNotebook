import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FaPlus, FaEdit, FaTrash, FaEye, FaPause, FaPlay, FaChartBar, FaTimes } from 'react-icons/fa';
import {
  adminGetDiscounts,
  adminDeleteDiscount,
  adminToggleDiscountStatus,
  adminGetDiscountUsage,
} from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';
import Modal from '../../components/Modal';

const DISCOUNT_TYPE_LABELS = {
  percentage: 'Percentage',
  flat: 'Flat',
  bundle: 'Bundle',
  bogo: 'BOGO',
  free_shipping: 'Free Shipping',
};

const STATUS_LABELS = {
  active: 'Active',
  inactive: 'Inactive',
};

function AdminDiscounts() {
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [discounts, setDiscounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [deleteModal, setDeleteModal] = useState({ show: false, id: null, name: '' });
  const [usageModal, setUsageModal] = useState({ show: false, discount: null, usages: [], totalUses: 0, totalApplied: 0, loading: false });

  const loadDiscounts = async (params = {}) => {
    try {
      setLoading(true);
      const data = await adminGetDiscounts(params);
      setDiscounts(data.discounts || []);
    } catch (err) {
      console.error('Failed to load discounts:', err);
      addToast(err.response?.data?.detail || 'Failed to load discounts.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await adminGetDiscounts({});
        if (mounted) setDiscounts(data.discounts || []);
      } catch (err) {
        if (mounted) addToast(err.response?.data?.detail || 'Failed to load discounts.', 'error');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchData();
    return () => { mounted = false; };
  }, []);

  const applyFilters = (params) => {
    loadDiscounts(params);
  };

  const handleTypeChange = (e) => {
    const val = e.target.value;
    setTypeFilter(val);
    const params = {};
    if (val) params.discount_type = val;
    if (statusFilter) params.status = statusFilter;
    applyFilters(params);
  };

  const handleStatusChange = (e) => {
    const val = e.target.value;
    setStatusFilter(val);
    const params = {};
    if (typeFilter) params.discount_type = typeFilter;
    if (val) params.status = val;
    applyFilters(params);
  };

  const handleToggleStatus = async (discount) => {
    try {
      const newStatus = discount.status === 'active' ? 'inactive' : 'active';
      await adminToggleDiscountStatus(discount.id, newStatus);
      setDiscounts(discounts.map(d =>
        d.id === discount.id ? { ...d, status: newStatus } : d
      ));
      addToast(`Discount "${discount.name}" ${newStatus === 'active' ? 'activated' : 'deactivated'}.`, 'success');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to update status.', 'error');
    }
  };

  const handleDelete = (id, name) => {
    setDeleteModal({ show: true, id, name });
  };

  const confirmDelete = async () => {
    const { id } = deleteModal;
    setDeleteModal({ show: false, id: null, name: '' });
    try {
      await adminDeleteDiscount(id);
      setDiscounts(discounts.filter(d => d.id !== id));
      addToast('Discount deleted successfully!', 'success');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to delete discount.', 'error');
    }
  };

  const handleViewUsage = async (discount) => {
    try {
      setUsageModal(prev => ({ ...prev, loading: true }));
      const data = await adminGetDiscountUsage(discount.id, { limit: 50 });
      setUsageModal({
        show: true,
        discount,
        usages: data.usages || [],
        totalUses: data.total_uses || 0,
        totalApplied: data.total_applied_amount || '0',
        loading: false,
      });
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to load usage data.', 'error');
      setUsageModal(prev => ({ ...prev, loading: false }));
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'percentage': return 'badge-info';
      case 'flat': return 'badge-blue';
      case 'bundle': return 'badge-purple';
      case 'bogo': return 'badge-warning';
      case 'free_shipping': return 'badge-success';
      default: return 'badge-gray';
    }
  };

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h2>Discounts</h2>
        <div className="header-actions">
          <button
            className="btn btn-primary"
            onClick={() => navigate('/admin/discounts/new')}
          >
            <FaPlus /> Add Discount
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="admin-filters">
        <select value={typeFilter} onChange={handleTypeChange} className="filter-select">
          <option value="">All Types</option>
          {Object.entries(DISCOUNT_TYPE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
        <select value={statusFilter} onChange={handleStatusChange} className="filter-select">
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>

      {/* Table */}
      {loading ? (
        <div className="loading">Loading discounts...</div>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Name</th>
                <th>Type</th>
                <th>Value</th>
                <th>Scope</th>
                <th>Status</th>
                <th>Start Date</th>
                <th>End Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {discounts.length === 0 ? (
                <tr>
                  <td colSpan="9" className="table-empty">
                    No discounts found. <Link to="/admin/discounts/new">Create one</Link>.
                  </td>
                </tr>
              ) : (
                discounts.map((discount, index) => {
                  const valueDisplay = discount.value_type
                    ? `${discount.value}${discount.value_type === 'percentage' ? '%' : '৳'}`
                    : discount.type === 'free_shipping'
                      ? 'Free Shipping'
                      : discount.type === 'bundle'
                        ? discount.bundle_rule
                          ? (discount.bundle_rule.bundle_type === 'quantity'
                            ? `${discount.bundle_rule.slabs?.length || 0} slab(s)`
                            : 'Combo')
                          : 'Bundle'
                        : discount.type === 'bogo'
                          ? `${discount.bogo_rule?.buy_quantity}+${discount.bogo_rule?.get_quantity}`
                          : '-';

                  const scopeDisplay = discount.scopes && discount.scopes.length > 0
                    ? discount.scopes.map(s => {
                        const name = s.scope_name;
                        const label = name || `#${s.scope_id}`;
                        const prefix = s.scope_type === 'product' ? 'Product ' : s.scope_type === 'category' ? 'Category ' : '';
                        return `${prefix}${label}`;
                      }).join(', ')
                    : discount.bundle_rule
                      ? (discount.bundle_rule.bundle_type === 'quantity'
                        ? 'Product-scoped'
                        : 'Multi-product')
                      : discount.bogo_rule
                        ? (discount.bogo_rule.product_names && discount.bogo_rule.product_names.length > 0
                            ? `Product: ${discount.bogo_rule.product_names.join(', ')}`
                            : `Product #${discount.bogo_rule.product_id}`)
                        : 'Global';

                  return (
                    <tr key={discount.id}>
                      <td>{index + 1}</td>
                      <td>
                        <div className="table-cell-primary">
                           {discount.name}
                           {(discount.free_shipping || discount.bundle_rule?.free_shipping) && (
                             <span className="badge badge-success badge-sm">🚚 FS</span>
                           )}
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${getTypeColor(discount.type)}`}>
                          {DISCOUNT_TYPE_LABELS[discount.type] || discount.type}
                        </span>
                      </td>
                      <td>{valueDisplay}</td>
                      <td>{scopeDisplay}</td>
                      <td>
                        <span className={`badge ${discount.status === 'active' ? 'badge-green' : 'badge-red'}`}>
                          {STATUS_LABELS[discount.status] || discount.status}
                        </span>
                      </td>
                      <td>{discount.start_date ? new Date(discount.start_date).toLocaleDateString() : '-'}</td>
                      <td>{discount.end_date ? new Date(discount.end_date).toLocaleDateString() : 'Never'}</td>
                      <td>
                        <div className="table-actions">
                          <button
                            className="action-btn action-view"
                            onClick={() => navigate(`/admin/discounts/${discount.id}`)}
                            aria-label={`View ${discount.name}`}
                            title="View / Edit"
                          >
                            <FaEye />
                          </button>
                          <button
                            className="action-btn action-edit"
                            onClick={() => navigate(`/admin/discounts/${discount.id}/edit`)}
                            aria-label={`Edit ${discount.name}`}
                          >
                            <FaEdit />
                          </button>
                          <button
                            className={`action-btn ${discount.status === 'active' ? 'action-pause' : 'action-play'}`}
                            onClick={() => handleToggleStatus(discount)}
                            aria-label={discount.status === 'active' ? 'Deactivate' : 'Activate'}
                            title={discount.status === 'active' ? 'Deactivate' : 'Activate'}
                          >
                            {discount.status === 'active' ? <FaPause /> : <FaPlay />}
                          </button>
                          <button
                            className="action-btn action-delete"
                            onClick={() => handleDelete(discount.id, discount.name)}
                            aria-label={`Delete ${discount.name}`}
                          >
                            <FaTrash />
                          </button>
                          <button
                            className="action-btn action-stats"
                            onClick={() => handleViewUsage(discount)}
                            aria-label={`View usage for ${discount.name}`}
                            title="Usage Stats"
                          >
                            <FaChartBar />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        isOpen={deleteModal.show}
        onClose={() => setDeleteModal({ show: false, id: null, name: '' })}
        onConfirm={confirmDelete}
        title="Delete Discount"
        message={`Are you sure you want to delete "${deleteModal.name}"? This action cannot be undone.`}
        confirmText="Delete"
        type="danger"
      />

      {usageModal.show && (
        <div className="admin-modal-overlay" onClick={() => setUsageModal(prev => ({ ...prev, show: false }))}>
          <div className="admin-modal-content usage-modal" onClick={(e) => e.stopPropagation()}>
            <div className="usage-modal-header">
              <h3>Usage: {usageModal.discount?.name}</h3>
              <button className="modal-close-btn" onClick={() => setUsageModal(prev => ({ ...prev, show: false }))}>
                <FaTimes />
              </button>
            </div>
            <div className="usage-stats">
              <div className="usage-stat">
                <span className="usage-stat-label">Total Uses</span>
                <span className="usage-stat-value">{usageModal.totalUses}</span>
              </div>
              <div className="usage-stat">
                <span className="usage-stat-label">Total Discount Given</span>
                <span className="usage-stat-value">৳{parseFloat(usageModal.totalApplied || 0).toLocaleString()}</span>
              </div>
            </div>
            <div className="usage-table-wrap">
              <table className="admin-table usage-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Order ID</th>
                    <th>Amount</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {usageModal.usages.length === 0 ? (
                    <tr><td colSpan="4" className="table-empty">No usage records yet</td></tr>
                  ) : (
                    usageModal.usages.map((u, idx) => (
                      <tr key={u.id}>
                        <td>{idx + 1}</td>
                        <td>#{u.order_id}</td>
                        <td>৳{parseFloat(u.applied_amount).toLocaleString()}</td>
                        <td>{new Date(u.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminDiscounts;
