import { useEffect, useState } from 'react';
import { FaPlus, FaEdit, FaTrash } from 'react-icons/fa';
import {
  adminGetCategories,
  adminCreateCategory,
  adminUpdateCategory,
  adminDeleteCategory,
} from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';
import Modal from '../../components/Modal';

function AdminCategories() {
  const { addToast } = useToast();
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    parent_id: '',
    is_active: true,
  });
  const [imageFile, setImageFile] = useState(null);
  const [deleteModal, setDeleteModal] = useState({ show: false, id: null, name: '' });

  const loadCategories = async () => {
    try {
      setLoading(true);
      const data = await adminGetCategories({ limit: 100 });
      setCategories(data.categories || []);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to load categories.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await adminGetCategories({ limit: 100 });
        if (mounted) setCategories(data.categories || []);
      } catch (err) {
        if (mounted) addToast(err.response?.data?.detail || 'Failed to load categories.', 'error');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchData();
    return () => { mounted = false; };
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({ ...formData, [name]: type === 'checkbox' ? checked : value });
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    setImageFile(file || null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const formDataObj = new FormData();
      formDataObj.append('name', formData.name);
      formDataObj.append('description', formData.description || '');
       if (formData.parent_id) formDataObj.append('parent_id', parseInt(formData.parent_id));
       else formDataObj.append('parent_id', '0');
      formDataObj.append('is_active', formData.is_active);
      if (imageFile) formDataObj.append('image', imageFile);

      if (editingCategory) {
        await adminUpdateCategory(editingCategory.id, formDataObj);
      } else {
        await adminCreateCategory(formDataObj);
      }

      setShowForm(false);
      setEditingCategory(null);
      setImageFile(null);
      setFormData({ name: '', description: '', parent_id: '', is_active: true });
      await loadCategories();
      addToast(editingCategory ? 'Category updated successfully!' : 'Category created successfully!', 'success');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to save category.', 'error');
    }
  };

  const handleEdit = (category) => {
    setEditingCategory(category);
    setFormData({
      name: category.name,
      description: category.description || '',
      parent_id: category.parent_id || '',
      is_active: category.is_active,
    });
    setImageFile(null);
    setShowForm(true);
  };

  const handleDelete = async (id, name) => {
    setDeleteModal({ show: true, id: id, name: name });
  };

  const confirmDelete = async () => {
    const { id } = deleteModal;
    setDeleteModal({ show: false, id: null, name: '' });
    try {
      await adminDeleteCategory(id);
      await loadCategories();
      addToast('Category deleted successfully!', 'success');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to delete category.', 'error');
    }
  };

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h2>Categories</h2>
        <button className="btn btn-primary" onClick={() => {
          setEditingCategory(null);
          setImageFile(null);
          setFormData({ name: '', description: '', parent_id: '', is_active: true });
          setShowForm(!showForm);
        }}>
          <FaPlus /> {showForm ? 'Cancel' : 'Add Category'}
        </button>
      </div>

      {showForm && (
        <form className="admin-form" onSubmit={handleSubmit}>
          <h3>{editingCategory ? 'Edit Category' : 'Add New Category'}</h3>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="cat-name">Name *</label>
              <input type="text" id="cat-name" name="name" value={formData.name} onChange={handleChange} required placeholder="Category name" />
            </div>
            <div className="form-group">
              <label htmlFor="cat-parent">Parent Category</label>
              <select id="cat-parent" name="parent_id" value={formData.parent_id} onChange={handleChange}>
                <option value="">None (Top Level)</option>
                {categories.filter((c) => c.id !== (editingCategory?.id || -1)).map((category) => (
                  <option key={category.id} value={category.id}>{category.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="cat-desc">Description</label>
            <textarea id="cat-desc" name="description" value={formData.description} onChange={handleChange} rows="2" placeholder="Category description" />
          </div>

          <div className="form-group">
            <label htmlFor="cat-image">Upload Category Image</label>
            <input type="file" id="cat-image" accept="image/*" onChange={handleImageChange} />
            {editingCategory?.image_url && (
              <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <img src={editingCategory.image_url} alt="Current" style={{ width: '50px', height: '50px', objectFit: 'cover', borderRadius: '8px' }} />
                <span style={{ fontSize: '12px', color: '#6b7280' }}>Current image (upload new to replace)</span>
              </div>
            )}
          </div>

          <div className="form-checkbox">
            <label>
              <input type="checkbox" name="is_active" checked={formData.is_active} onChange={handleChange} />
              Active
            </label>
          </div>

          <button type="submit" className="btn btn-primary">
            {editingCategory ? 'Update Category' : 'Create Category'}
          </button>
        </form>
      )}

      {loading ? (
        <div className="loading">Loading categories...</div>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Image</th>
                <th>Name</th>
                <th>Slug</th>
                <th>Parent</th>
                <th>Description</th>
                <th>Active</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {categories.length === 0 ? (
                <tr><td colSpan="8" className="table-empty">No categories found</td></tr>
              ) : (
                categories.map((category, index) => (
                  <tr key={category.id}>
                    <td>{index + 1}</td>
                    <td>
                      {category.image_url ? (
                        <img src={category.image_url} alt={category.name} className="table-image" />
                      ) : (
                        <span style={{ display:'flex', alignItems:'center', justifyContent:'center', width:'60px', height:'40px', fontSize:'24px', background:'#f3f4f6', borderRadius:'8px' }}>📚</span>
                      )}
                    </td>
                    <td>{category.name}</td>
                    <td>{category.slug}</td>
                    <td>{category.parent_id ? (categories.find((c) => c.id === category.parent_id)?.name || `#${category.parent_id}`) : '-'}</td>
                    <td>{category.description || '-'}</td>
                    <td>
                      <span className={`badge ${category.is_active ? 'badge-green' : 'badge-red'}`}>
                        {category.is_active ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td>
                      <div className="table-actions">
                        <button className="action-btn action-edit" onClick={() => handleEdit(category)} aria-label={`Edit ${category.name}`}>
                          <FaEdit />
                        </button>
                        <button className="action-btn action-delete" onClick={() => handleDelete(category.id, category.name)} aria-label={`Delete ${category.name}`}>
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

      <Modal
        isOpen={deleteModal.show}
        onClose={() => setDeleteModal({ show: false, id: null, name: '' })}
        onConfirm={confirmDelete}
        title="Delete Category"
        message={`Are you sure you want to delete "${deleteModal.name}"? This will also delete its subcategories and products.`}
        confirmText="Delete"
        type="danger"
      />
    </div>
  );
}

export default AdminCategories;