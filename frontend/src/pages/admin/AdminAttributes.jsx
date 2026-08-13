import { useEffect, useState } from 'react';
import { FaPlus, FaEdit, FaTrash, FaList } from 'react-icons/fa';
import {
  adminGetAttributes,
  adminCreateAttribute,
  adminUpdateAttribute,
  adminDeleteAttribute,
} from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';
import Modal from '../../components/Modal';

function AdminAttributes() {
  const { addToast } = useToast();
  const [attributes, setAttributes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingAttribute, setEditingAttribute] = useState(null);
  const [formData, setFormData] = useState({ name: '', is_active: true });
  const [deleteModal, setDeleteModal] = useState({ show: false, id: null, name: '' });

  const loadAttributes = async () => {
    try {
      setLoading(true);
      const data = await adminGetAttributes({ limit: 100 });
      setAttributes(data.attributes || []);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to load attributes.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAttributes();
  }, []);

  const resetForm = () => {
    setFormData({ name: '', is_active: true });
    setEditingAttribute(null);
  };

  const openCreateModal = () => {
    resetForm();
    setShowModal(true);
  };

  const openEditModal = (attribute) => {
    setEditingAttribute(attribute);
    setFormData({
      name: attribute.name,
      is_active: attribute.is_active,
    });
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    resetForm();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingAttribute) {
        await adminUpdateAttribute(editingAttribute.id, formData);
      } else {
        await adminCreateAttribute(formData);
      }
      closeModal();
      await loadAttributes();
      addToast(editingAttribute ? 'Attribute updated successfully!' : 'Attribute created successfully!', 'success');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to save attribute.', 'error');
    }
  };

  const handleDelete = async (id, name) => {
    setDeleteModal({ show: true, id: id, name: name });
  };

  const confirmDelete = async () => {
    const { id } = deleteModal;
    setDeleteModal({ show: false, id: null, name: '' });
    try {
      await adminDeleteAttribute(id);
      await loadAttributes();
      addToast('Attribute deleted successfully!', 'success');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to delete attribute.', 'error');
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h2>Attributes</h2>
        <button className="btn btn-primary" onClick={openCreateModal}>
          <FaPlus /> Add Attribute
        </button>
      </div>

      {loading ? (
        <div className="loading">Loading attributes...</div>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Name</th>
                <th>Slug</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {attributes.length === 0 ? (
                <tr>
                  <td colSpan="6" className="table-empty">No attributes found</td>
                </tr>
              ) : (
                attributes.map((attr, index) => (
                  <tr key={attr.id}>
                    <td>{index + 1}</td>
                    <td>{attr.name}</td>
                    <td>{attr.slug}</td>
                    <td>
                      <span className={`badge ${attr.is_active ? 'badge-green' : 'badge-red'}`}>
                        {attr.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>{new Date(attr.created_at).toLocaleDateString()}</td>
                    <td>
<div className="table-actions">
                      <button
                        className="action-btn action-edit"
                        onClick={() => openEditModal(attr)}
                        aria-label={`Edit ${attr.name}`}
                      >
                        <FaEdit />
                      </button>
                      <button
                        className="action-btn action-delete"
                        onClick={() => handleDelete(attr.id, attr.name)}
                        aria-label={`Delete ${attr.name}`}
                      >
                        <FaTrash />
                      </button>
                      <button
                        className="action-btn action-view"
                        onClick={() => window.location.href = `/admin/attribute-options?attribute_id=${attr.id}`}
                        aria-label={`View options for ${attr.name}`}
                      >
                        <FaList />
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

      {showModal && (
        <div className="modal-overlay" onClick={(e) => {
          if (e.target === e.currentTarget) {
            closeModal();
          }
        }}>
          <div className="modal">
            <div className="modal-header">
              <h3>{editingAttribute ? 'Edit Attribute' : 'Add Attribute'}</h3>
              <button className="modal-close" onClick={closeModal}>&times;</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label htmlFor="name">Attribute Name *</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    required
                    placeholder="e.g., Color, Size, Material"
                  />
                </div>
                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      name="is_active"
                      checked={formData.is_active}
                      onChange={handleInputChange}
                    />
                    <span>Active</span>
                  </label>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={closeModal}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingAttribute ? 'Update' : 'Create'}
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
        title="Delete Attribute"
        message={`Are you sure you want to delete "${deleteModal.name}"? This will also delete all associated attribute options.`}
        confirmText="Delete"
        type="danger"
      />
    </div>
  );
}

export default AdminAttributes;