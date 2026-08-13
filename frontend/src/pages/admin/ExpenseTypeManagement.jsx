import { useEffect, useState } from 'react';
import { FaEdit, FaTrash } from 'react-icons/fa';
import {
  adminGetExpenseTypes,
  adminCreateExpenseType,
  adminUpdateExpenseType,
  adminDeleteExpenseType,
} from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';
import Modal from '../../components/Modal';

function ExpenseTypeManagement() {
  const { addToast } = useToast();
  const [types, setTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingType, setEditingType] = useState(null);
  const [formData, setFormData] = useState({ name: '', description: '', is_active: true });
  const [deleteModal, setDeleteModal] = useState({ show: false, id: null, name: '' });

  const loadTypes = async () => {
    try {
      setLoading(true);
      const data = await adminGetExpenseTypes({ limit: 100 });
      setTypes(data.expense_types || []);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to load expense types.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTypes();
  }, []);

  const resetForm = () => {
    setFormData({ name: '', description: '', is_active: true });
  };

  const handleEdit = (type) => {
    setEditingType(type);
    setFormData({ name: type.name, description: type.description || '', is_active: type.is_active });
    setShowForm(true);
  };

  const handleDelete = (type) => {
    setDeleteModal({ show: true, id: type.id, name: type.name });
  };

  const confirmDelete = async () => {
    const { id } = deleteModal;
    setDeleteModal({ show: false, id: null, name: '' });
    try {
      await adminDeleteExpenseType(id);
      addToast('Expense type deleted successfully!', 'success');
      loadTypes();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to delete expense type.', 'error');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingType) {
        await adminUpdateExpenseType(editingType.id, formData);
        addToast('Expense type updated successfully!', 'success');
      } else {
        await adminCreateExpenseType(formData);
        addToast('Expense type created successfully!', 'success');
      }
      setShowForm(false);
      setEditingType(null);
      resetForm();
      loadTypes();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to save expense type.', 'error');
    }
  };

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h2>Expense Types</h2>
        <button className="btn btn-primary" onClick={() => { setEditingType(null); setShowForm(true); resetForm(); }}>
          + Add Expense Type
        </button>
      </div>

      {loading ? (
        <div className="loading">Loading expense types...</div>
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
              {types.length === 0 ? (
                <tr><td colSpan="5" className="table-empty">No expense types found</td></tr>
              ) : (
                types.map((type, index) => (
                  <tr key={type.id}>
                    <td>{index + 1}</td>
                    <td>{type.name}</td>
                    <td>{type.description || '—'}</td>
                    <td>
                      <span className={`status-badge ${type.is_active ? 'status-paid' : 'status-due'}`}>
                        {type.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <div className="table-actions">
                        <button className="action-btn action-edit" onClick={() => handleEdit(type)} aria-label={`Edit ${type.name}`}>
                          <FaEdit />
                        </button>
                        <button className="action-btn action-delete" onClick={() => handleDelete(type)} aria-label={`Delete ${type.name}`}>
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
        <div className="modal-overlay" onClick={() => { setShowForm(false); setEditingType(null); }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingType ? 'Edit Expense Type' : 'Add Expense Type'}</h3>
              <button className="modal-close" onClick={() => { setShowForm(false); setEditingType(null); }}>×</button>
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
                    placeholder="Expense type name"
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
                <button type="button" className="btn btn-secondary" onClick={() => { setShowForm(false); setEditingType(null); }}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingType ? 'Update' : 'Create'}
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
        title="Delete Expense Type"
        message={`Are you sure you want to delete "${deleteModal.name}"?`}
        confirmText="Delete"
        type="danger"
      />
    </div>
  );
}

export default ExpenseTypeManagement;
