import { useEffect, useState } from 'react';
import { FaPlus, FaEdit, FaTrash } from 'react-icons/fa';
import {
  adminGetShippingCharges,
  adminCreateShippingCharge,
  adminUpdateShippingCharge,
  adminDeleteShippingCharge,
} from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';
import Modal from '../../components/Modal';

function AdminShippingCharges() {
  const { addToast } = useToast();
  const [charges, setCharges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingCharge, setEditingCharge] = useState(null);
  const [formData, setFormData] = useState({
    zone_name: '',
    amount: '',
    is_active: true,
  });
  const [deleteModal, setDeleteModal] = useState({ show: false, id: null, zone_name: '' });

  const loadCharges = async () => {
    try {
      setLoading(true);
      const data = await adminGetShippingCharges();
      setCharges(data.shipping_charges || []);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to load shipping charges.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await adminGetShippingCharges();
        if (mounted) setCharges(data.shipping_charges || []);
      } catch (err) {
        if (mounted) addToast(err.response?.data?.detail || 'Failed to load shipping charges.', 'error');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchData();
    return () => { mounted = false; };
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : name === 'amount' ? value : value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (!formData.zone_name.trim()) {
        addToast('Zone name is required.', 'error');
        return;
      }
      if (formData.amount === '' || parseInt(formData.amount) < 0) {
        addToast('Please enter a valid non-negative amount.', 'error');
        return;
      }

      const payload = {
        zone_name: formData.zone_name.trim(),
        amount: parseInt(formData.amount),
        is_active: formData.is_active,
      };

      if (editingCharge) {
        await adminUpdateShippingCharge(editingCharge.id, payload);
        addToast('Shipping charge updated successfully.', 'success');
      } else {
        await adminCreateShippingCharge(payload);
        addToast('Shipping charge created successfully.', 'success');
      }

      setShowForm(false);
      setEditingCharge(null);
      setFormData({ zone_name: '', amount: '', is_active: true });
      await loadCharges();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to save shipping charge.', 'error');
    }
  };

  const handleEdit = (charge) => {
    setEditingCharge(charge);
    setFormData({
      zone_name: charge.zone_name,
      amount: charge.amount,
      is_active: charge.is_active,
    });
    setShowForm(true);
  };

  const handleDelete = async () => {
    try {
      await adminDeleteShippingCharge(deleteModal.id);
      addToast('Shipping charge deleted successfully.', 'success');
      setDeleteModal({ show: false, id: null, zone_name: '' });
      await loadCharges();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to delete shipping charge.', 'error');
    }
  };

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <div>
          <h2>Shipping Charges</h2>
          <p className="admin-subtitle">Manage delivery charges by zone. This is for display only and does not affect order totals.</p>
        </div>
        <button className="btn btn-primary" onClick={() => { setShowForm(true); setEditingCharge(null); setFormData({ zone_name: '', amount: '', is_active: true }); }}>
          <FaPlus /> Add Zone
        </button>
      </div>

      {showForm && (
        <form className="admin-form" onSubmit={handleSubmit} style={{ marginBottom: '24px' }}>
          <h3>{editingCharge ? 'Edit Shipping Charge' : 'Add Shipping Charge'}</h3>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="zone_name">Zone Name *</label>
              <input type="text" id="zone_name" name="zone_name" value={formData.zone_name} onChange={handleChange} placeholder="e.g., Inside Dhaka, Outside Dhaka" required />
            </div>
            <div className="form-group">
              <label htmlFor="amount">Delivery Charge (৳) *</label>
              <input type="number" id="amount" name="amount" value={formData.amount} onChange={handleChange} placeholder="e.g., 60" min="0" required />
            </div>
          </div>
          <div className="form-checkbox">
            <label>
              <input type="checkbox" name="is_active" checked={formData.is_active} onChange={handleChange} />
              Active
            </label>
          </div>
          <div className="form-actions">
            <button type="button" className="btn btn-outline" onClick={() => { setShowForm(false); setEditingCharge(null); setFormData({ zone_name: '', amount: '', is_active: true }); }}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              {editingCharge ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="loading">Loading shipping charges...</div>
      ) : charges.length === 0 ? (
        <div className="table-empty">No shipping charges found. Add your first zone to get started.</div>
      ) : (
        <div className="table-container">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Zone</th>
                <th>Amount (৳)</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {charges.map((charge) => (
                <tr key={charge.id}>
                  <td>{charge.zone_name}</td>
                  <td>৳{charge.amount}</td>
                  <td>
                    <span className={`badge ${charge.is_active ? 'badge-green' : 'badge-red'}`}>
                      {charge.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>{new Date(charge.created_at).toLocaleDateString()}</td>
                  <td>
                    <div className="table-actions">
                      <button className="btn btn-outline btn-sm" onClick={() => handleEdit(charge)}>
                        <FaEdit /> Edit
                      </button>
                      <button className="btn btn-danger btn-sm" onClick={() => setDeleteModal({ show: true, id: charge.id, zone_name: charge.zone_name })}>
                        <FaTrash /> Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <Modal isOpen={deleteModal.show} onClose={() => setDeleteModal({ show: false, id: null, zone_name: '' })} title="Delete Shipping Charge">
        <p>Are you sure you want to delete the shipping charge for <strong>{deleteModal.zone_name}</strong>?</p>
        <div className="form-actions">
          <button className="btn btn-outline" onClick={() => setDeleteModal({ show: false, id: null, zone_name: '' })}>Cancel</button>
          <button className="btn btn-danger" onClick={handleDelete}>Delete</button>
        </div>
      </Modal>
    </div>
  );
}

export default AdminShippingCharges;
