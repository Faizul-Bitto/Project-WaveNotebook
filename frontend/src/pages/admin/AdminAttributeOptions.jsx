import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { FaPlus, FaEdit, FaTrash, FaArrowLeft } from 'react-icons/fa';
import {
  adminGetAttributeOptions,
  adminCreateAttributeOption,
  adminUpdateAttributeOption,
  adminDeleteAttributeOption,
} from '../../api/adminServices';

function AdminAttributeOptions() {
  const [searchParams, setSearchParams] = useSearchParams();
  const attributeId = searchParams.get('attribute_id');
  
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingOption, setEditingOption] = useState(null);
  const [formData, setFormData] = useState({ 
    attribute_id: attributeId ? parseInt(attributeId) : '', 
    value: '', 
    additional_price: '' 
  });

  const loadOptions = async () => {
    if (!attributeId) return;
    try {
      setLoading(true);
      const data = await adminGetAttributeOptions({ 
        attribute_id: parseInt(attributeId),
        limit: 100 
      });
      setOptions(data.options || []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load attribute options.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOptions();
  }, [attributeId]);

  const resetForm = () => {
    setFormData({ 
      attribute_id: attributeId ? parseInt(attributeId) : '', 
      value: '', 
      additional_price: '' 
    });
    setEditingOption(null);
  };

  const openCreateModal = () => {
    resetForm();
    setShowModal(true);
  };

  const openEditModal = (option) => {
    setEditingOption(option);
    setFormData({
      attribute_id: option.attribute_id,
      value: option.value,
      additional_price: parseFloat(option.additional_price),
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
      if (editingOption) {
        await adminUpdateAttributeOption(editingOption.id, formData);
      } else {
        await adminCreateAttributeOption(formData);
      }
      closeModal();
      await loadOptions();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to save attribute option.');
    }
  };

  const handleDelete = async (id, value) => {
    if (window.confirm(`Are you sure you want to delete "${value}"?`)) {
      try {
        await adminDeleteAttributeOption(id);
        await loadOptions();
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to delete attribute option.');
      }
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  if (!attributeId) {
    return (
      <div className="admin-page">
        <div className="admin-page-header">
          <h2>Attribute Options</h2>
        </div>
        <div className="alert alert-warning">
          Please select an attribute from the <strong>Attributes</strong> page to manage its options.
        </div>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h2>Attribute Options</h2>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={() => setSearchParams({})}>
            <FaArrowLeft /> Back to Attributes
          </button>
          <button className="btn btn-primary" onClick={openCreateModal}>
            <FaPlus /> Add Option
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="loading">Loading attribute options...</div>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Value</th>
                <th>Additional Price</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {options.length === 0 ? (
                <tr>
                  <td colSpan="5" className="table-empty">No attribute options found. Click "Add Option" to create one.</td>
                </tr>
              ) : (
                options.map((option) => (
                  <tr key={option.id}>
                    <td>{option.id}</td>
                    <td>{option.value}</td>
                    <td>৳{parseFloat(option.additional_price).toLocaleString()}</td>
                    <td>{new Date(option.created_at).toLocaleDateString()}</td>
                    <td className="table-actions">
                      <button
                        className="action-btn action-edit"
                        onClick={() => openEditModal(option)}
                        aria-label={`Edit ${option.value}`}
                      >
                        <FaEdit />
                      </button>
                      <button
                        className="action-btn action-delete"
                        onClick={() => handleDelete(option.id, option.value)}
                        aria-label={`Delete ${option.value}`}
                      >
                        <FaTrash />
                      </button>
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
              <h3>{editingOption ? 'Edit Attribute Option' : 'Add Attribute Option'}</h3>
              <button className="modal-close" onClick={closeModal}>&times;</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label htmlFor="value">Option Value *</label>
                  <input
                    type="text"
                    id="value"
                    name="value"
                    value={formData.value}
                    onChange={handleInputChange}
                    required
                    placeholder="e.g., Red, Large, Cotton"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="additional_price">Additional Price (৳)</label>
                  <input
                    type="number"
                    id="additional_price"
                    name="additional_price"
                    value={formData.additional_price}
                    onChange={handleInputChange}
                    min="0"
                    step="0.01"
                    placeholder="0.00"
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={closeModal}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingOption ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminAttributeOptions;