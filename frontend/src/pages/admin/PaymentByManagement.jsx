import { useEffect, useState } from 'react';
import { FaEdit, FaTrash } from 'react-icons/fa';
import {
  adminGetPaymentByList,
  adminCreatePaymentBy,
  adminUpdatePaymentBy,
  adminDeletePaymentBy,
} from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';
import Modal from '../../components/Modal';

function PaymentByManagement() {
  const { addToast } = useToast();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({ name: '', description: '', is_active: true });
  const [deleteModal, setDeleteModal] = useState({ show: false, id: null, name: '' });

  const loadItems = async () => {
    try {
      setLoading(true);
      const data = await adminGetPaymentByList({ limit: 100 });
      setItems(data.items || []);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to load payment by list.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadItems();
  }, []);

  const resetForm = () => {
    setFormData({ name: '', description: '', is_active: true });
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setFormData({ name: item.name, description: item.description || '', is_active: item.is_active });
    setShowForm(true);
  };

  const handleDelete = (item) => {
    setDeleteModal({ show: true, id: item.id, name: item.name });
  };

  const confirmDelete = async () => {
    const { id } = deleteModal;
    setDeleteModal({ show: false, id: null, name: '' });
    try {
      await adminDeletePaymentBy(id);
      addToast('Person deleted successfully!', 'success');
      loadItems();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to delete person.', 'error');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingItem) {
        await adminUpdatePaymentBy(editingItem.id, formData);
        addToast('Person updated successfully!', 'success');
      } else {
        await adminCreatePaymentBy(formData);
        addToast('Person added successfully!', 'success');
      }
      setShowForm(false);
      setEditingItem(null);
      resetForm();
      loadItems();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to save person.', 'error');
    }
  };

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h2>Payment By</h2>
        <button className="btn btn-primary" onClick={() => { setEditingItem(null); setShowForm(true); resetForm(); }}>
          + Add Person
        </button>
      </div>

      {loading ? (
        <div className="loading">Loading payment by list...</div>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Name</th>
                <th>Description</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr><td colSpan="5" className="table-empty">No persons found</td></tr>
              ) : (
                items.map((item, index) => (
                  <tr key={item.id}>
                    <td>{index + 1}</td>
                    <td>{item.name}</td>
                    <td>{item.description || '—'}</td>
                    <td>
                      <span className={`status-badge ${item.is_active ? 'status-paid' : 'status-due'}`}>
                        {item.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <div className="table-actions">
                        <button className="action-btn action-edit" onClick={() => handleEdit(item)} aria-label={`Edit ${item.name}`}>
                          <FaEdit />
                        </button>
                        <button className="action-btn action-delete" onClick={() => handleDelete(item)} aria-label={`Delete ${item.name}`}>
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
        <div className="modal-overlay" onClick={() => { setShowForm(false); setEditingItem(null); }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingItem ? 'Edit Person' : 'Add Person'}</h3>
              <button className="modal-close" onClick={() => { setShowForm(false); setEditingItem(null); }}>×</button>
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
                    placeholder="Person name"
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
                <button type="button" className="btn btn-secondary" onClick={() => { setShowForm(false); setEditingItem(null); }}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingItem ? 'Update' : 'Create'}
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
        title="Delete Person"
        message={`Are you sure you want to delete "${deleteModal.name}"?`}
        confirmText="Delete"
        type="danger"
      />
    </div>
  );
}

export default PaymentByManagement;
