import { useEffect, useState } from 'react';
import { FaPlus, FaEdit, FaTrash } from 'react-icons/fa';
import {
  adminGetBanners,
  adminCreateBanner,
  adminUpdateBanner,
  adminDeleteBanner,
} from '../../api/adminServices';

function AdminBanners() {
  const [banners, setBanners] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingBanner, setEditingBanner] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    subtitle: '',
    link_url: '',
    sort_order: 0,
    is_active: true,
  });
  const [imageFile, setImageFile] = useState(null);

  const loadBanners = async () => {
    try {
      setLoading(true);
      const data = await adminGetBanners();
      setBanners(data.banners || []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load banners.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await adminGetBanners();
        if (mounted) setBanners(data.banners || []);
        if (mounted) setError(null);
      } catch (err) {
        if (mounted) setError(err.response?.data?.detail || 'Failed to load banners.');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchData();
    return () => {
      mounted = false;
    };
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : name === 'sort_order' ? parseInt(value) || 0 : value,
    });
  };

  const handleImageChange = (e) => {
    setImageFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const form = new FormData();
      form.append('title', formData.title);
      if (formData.subtitle) form.append('subtitle', formData.subtitle);
      if (formData.link_url) form.append('link_url', formData.link_url);
      form.append('sort_order', formData.sort_order);
      form.append('is_active', formData.is_active);

      if (editingBanner) {
        if (imageFile) form.append('image', imageFile);
        await adminUpdateBanner(editingBanner.id, form);
      } else {
        if (!imageFile) {
          alert('Please select a banner image.');
          return;
        }
        form.append('image', imageFile);
        await adminCreateBanner(form);
      }

      setShowForm(false);
      setEditingBanner(null);
      setFormData({ title: '', subtitle: '', link_url: '', sort_order: 0, is_active: true });
      setImageFile(null);
      await loadBanners();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to save banner.');
    }
  };

  const handleEdit = (banner) => {
    setEditingBanner(banner);
    setFormData({
      title: banner.title,
      subtitle: banner.subtitle || '',
      link_url: banner.link_url || '',
      sort_order: banner.sort_order,
      is_active: banner.is_active,
    });
    setShowForm(true);
  };

  const handleDelete = async (id, title) => {
    if (window.confirm(`Are you sure you want to delete banner "${title}"?`)) {
      try {
        await adminDeleteBanner(id);
        await loadBanners();
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to delete banner.');
      }
    }
  };

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h2>Banners</h2>
        <button className="btn btn-primary" onClick={() => {
          setEditingBanner(null);
          setFormData({ title: '', subtitle: '', link_url: '', sort_order: 0, is_active: true });
          setImageFile(null);
          setShowForm(!showForm);
        }}>
          <FaPlus /> {showForm ? 'Cancel' : 'Add Banner'}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Form */}
      {showForm && (
        <form className="admin-form" onSubmit={handleSubmit}>
          <h3>{editingBanner ? 'Edit Banner' : 'Add New Banner'}</h3>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="banner-title">Title *</label>
              <input
                type="text"
                id="banner-title"
                name="title"
                value={formData.title}
                onChange={handleChange}
                required
                placeholder="Banner title"
              />
            </div>
            <div className="form-group">
              <label htmlFor="banner-order">Sort Order</label>
              <input
                type="number"
                id="banner-order"
                name="sort_order"
                value={formData.sort_order}
                onChange={handleChange}
                min="0"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="banner-subtitle">Subtitle</label>
            <input
              type="text"
              id="banner-subtitle"
              name="subtitle"
              value={formData.subtitle}
              onChange={handleChange}
              placeholder="Banner subtitle"
            />
          </div>

          <div className="form-group">
            <label htmlFor="banner-link">Link URL</label>
            <input
              type="text"
              id="banner-link"
              name="link_url"
              value={formData.link_url}
              onChange={handleChange}
              placeholder="https://..."
            />
          </div>

          <div className="form-group">
            <label htmlFor="banner-image">
              {editingBanner ? 'New Image (optional)' : 'Banner Image *'}
            </label>
            <input
              type="file"
              id="banner-image"
              accept="image/*"
              onChange={handleImageChange}
            />
          </div>

          {editingBanner && (
            <div className="form-group">
              <img
                src={editingBanner.image_url}
                alt="Current banner"
                className="banner-preview"
              />
            </div>
          )}

          <div className="form-checkbox">
            <label>
              <input
                type="checkbox"
                name="is_active"
                checked={formData.is_active}
                onChange={handleChange}
              />
              Active
            </label>
          </div>

          <button type="submit" className="btn btn-primary">
            {editingBanner ? 'Update Banner' : 'Create Banner'}
          </button>
        </form>
      )}

      {/* Table */}
      {loading ? (
        <div className="loading">Loading banners...</div>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Image</th>
                <th>Title</th>
                <th>Subtitle</th>
                <th>Sort</th>
                <th>Active</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {banners.length === 0 ? (
                <tr>
                  <td colSpan="7" className="table-empty">No banners found</td>
                </tr>
              ) : (
                banners.map((banner) => (
                  <tr key={banner.id}>
                    <td>{banner.id}</td>
                    <td>
                      <img src={banner.image_url} alt={banner.title} className="table-image" />
                    </td>
                    <td>{banner.title}</td>
                    <td>{banner.subtitle || '-'}</td>
                    <td>{banner.sort_order}</td>
                    <td>
                      <span className={`badge ${banner.is_active ? 'badge-green' : 'badge-red'}`}>
                        {banner.is_active ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td className="table-actions">
                      <button
                        className="action-btn action-edit"
                        onClick={() => handleEdit(banner)}
                        aria-label={`Edit ${banner.title}`}
                      >
                        <FaEdit />
                      </button>
                      <button
                        className="action-btn action-delete"
                        onClick={() => handleDelete(banner.id, banner.title)}
                        aria-label={`Delete ${banner.title}`}
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
    </div>
  );
}

export default AdminBanners;