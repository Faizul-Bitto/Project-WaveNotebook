import { useEffect, useState } from 'react';
import { FaEdit, FaTrash } from 'react-icons/fa';
import {
  adminGetPaymentMethods,
  adminCreatePaymentMethod,
  adminUpdatePaymentMethod,
  adminDeletePaymentMethod,
} from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';
import Modal from '../../components/Modal';

function PaymentMethodManagement() {
  const { addToast } = useToast();
  const [methods, setMethods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingMethod, setEditingMethod] = useState(null);
  const [formData, setFormData] = useState({ name: '', description: '', is_active: true });
  const [deleteModal, setDeleteModal] = useState({ show: false, id: null, name: '' });

  const loadMethods = async () => {
    try {
      setLoading(true);
      const data = await adminGetPaymentMethods({ limit: 100 });
      setMethods(data.items || []);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to load payment methods.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMethods();
  }, []);

  const resetForm = () => {
    setFormData({ name: '', description: '', is_active: true });
  };

  const handleEdit = (method) => {
    setEditingMethod(method);
    setFormData({ name: method.name, description: method.description || '', is_active: method.is_active });
    setShowForm(true);
  };

  const handleDelete = (method) => {
    setDeleteModal({ show: true, id: method.id, name: method.name });
  };

  const confirmDelete = async () => {
    const { id } = deleteModal;
    setDeleteModal({ show: false, id: null, name: '' });
    try {
      await adminDeletePaymentMethod(id);
      addToast('Payment method deleted successfully!', 'success');
      loadMethods();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to delete payment method.', 'error');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingMethod) {
        await adminUpdatePaymentMethod(editingMethod.id, formData);
        addToast('Payment method updated successfully!', 'success');
      } else {
        await adminCreatePaymentMethod(formData);
        addToast('Payment method created successfully!', 'success');
      }
      setShowForm(false);
      setEditingMethod(null);
      resetForm();
      loadMethods();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to save payment method.', 'error');
    }
  };

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h2>Payment Methods</h2>
        <button className="btn btn-primary" onClick={() => { setEditingMethod(null); setShowForm(true); resetForm(); }}>
          + Add Payment Method
        </button>
      </div>

      {loading ? (
        <div className="loading">Loading payment methods...</div>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Description</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {methods.length === 0 ? (
                <tr><td colSpan="5" className="table-empty">No payment methods found</td></tr>
              ) : (
                methods.map((method) => (
                  <tr key={method.id}>
                    <td>{method.id}</td>
                    <td>{method.name}</td>
                    <td>{method.description || '—'}</td>
                    <td>
                      <span className={`status-badge ${method.is_active ? 'status-paid' : 'status-due'}`}>
                        {method.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <div className="table-actions">
                        <button className="action-btn action-edit" onClick={() => handleEdit(method)} aria-label={`Edit ${method.name}`}>
                          <FaEdit />
                        </button>
                        <button className="action-btn action-delete" onClick={() => handleDelete(method)} aria-label={`Delete ${method.name}`}>
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

      {showForm && (
        <div className="modal-overlay" onClick={() => { setShowForm(false); setEditingMethod(null); }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingMethod ? 'Edit Payment Method' : 'Add Payment Method'}</h3>
              <button className="modal-close" onClick={() => { setShowForm(false); setEditingMethod(null); }}>×</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    placeholder="Payment method name"
                  />
                </div>
                <div className="form-group">
                  <label>Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows="3"
                    placeholder="Optional description"
                  />
                </div>
                <div className="form-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    />
                    {' Active'}
                  </label>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => { setShowForm(false); setEditingMethod(null); }}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingMethod ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <Modal
        isOpen={deleteModal.show}
        onClose={() => setDeleteModal({ show: false, id: null, name: '' })}
        onConfirm={confirmDelete}
        title="Delete Payment Method"
        message={`Are you sure you want to delete "${deleteModal.name}"?`}
        confirmText="Delete"
        type="danger"
      />
    </div>
  );
}

export default PaymentMethodManagement;
