import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaPlus, FaEdit, FaTrash, FaCubes, FaSearch } from 'react-icons/fa';
import {
  adminGetProducts,
  adminDeleteProduct,
  adminToggleProductFeatured,
  adminGetCategories,
} from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';
import Modal from '../../components/Modal';
import Pagination from '../../components/Pagination';

const PAGE_SIZE = 20;

function AdminProducts() {
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [togglingId, setTogglingId] = useState(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState('');
  const [featuredFilter, setFeaturedFilter] = useState('');
  const [deleteModal, setDeleteModal] = useState({ show: false, id: null, name: '' });

  // Fetch products on mount or when page/filter changes
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const params = {
          skip: page * PAGE_SIZE,
          limit: PAGE_SIZE,
        };
        if (search) params.search = search;
        if (categoryFilter) params.category_id = categoryFilter;
        if (activeFilter) params.is_active = activeFilter === 'active';
        if (featuredFilter) params.is_featured = featuredFilter === 'featured';

        const data = await adminGetProducts(params);
        const fetched = data.products || [];
        setProducts(fetched);
        setTotal(data.total || 0);
      } catch (err) {
        addToast(err.response?.data?.detail || 'Failed to load products.', 'error');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [page, search, categoryFilter, activeFilter, featuredFilter, addToast]);

  // Load categories for the filter dropdown
  useEffect(() => {
    const loadCategories = async () => {
      try {
        const data = await adminGetCategories({ limit: 1000 });
        setCategories(data.categories || []);
      } catch (err) {
        console.error('Failed to load categories:', err);
      }
    };
    loadCategories();
  }, []);

  const handleDelete = async (id, name) => {
    setDeleteModal({ show: true, id: id, name: name });
  };

  const confirmDelete = async () => {
    const { id } = deleteModal;
    setDeleteModal({ show: false, id: null, name: '' });
    try {
      await adminDeleteProduct(id);
      setPage(0);
      addToast('Product deleted successfully!', 'success');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to delete product.', 'error');
    }
  };

  const handleEdit = (id) => {
    navigate(`/admin/products/${id}/edit`);
  };

  const handleViewVariants = (id) => {
    navigate(`/admin/products/${id}/variants`);
  };

  const handleToggleFeatured = async (id, current) => {
    setTogglingId(id);
    try {
      const newValue = !current;
      await adminToggleProductFeatured(id, newValue);
      setProducts((prev) =>
        prev.map((p) =>
          p.id === id ? { ...p, is_featured: newValue } : p
        )
      );
      addToast(
        `Product ${newValue ? 'marked as' : 'removed from'} featured.`,
        'success'
      );
    } catch (err) {
      addToast(
        err.response?.data?.detail || 'Failed to update featured status.',
        'error'
      );
    } finally {
      setTogglingId(null);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const trimmed = searchInput.trim();
    if (trimmed === search && trimmed !== '') return;
    setSearch(trimmed);
    setPage(0);
  };

  const handleClearSearch = () => {
    setSearchInput('');
    setSearch('');
    setPage(0);
  };

  const handleClearCategory = () => {
    setCategoryFilter('');
    setPage(0);
  };

  const handlePageChange = (newPage) => {
    const maxPage = Math.max(0, Math.ceil(total / PAGE_SIZE) - 1);
    setPage(Math.min(newPage, maxPage));
  };

  const handleCreate = () => {
    navigate('/admin/products/new');
  };

  const totalPages = Math.ceil(total / PAGE_SIZE) || 1;

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h2>Products</h2>
        <button className="btn btn-primary" onClick={handleCreate}>
          <FaPlus /> Add Product
        </button>
      </div>

      {/* Search & Filters */}
      <div className="admin-filters">
        <form className="admin-filter-row" onSubmit={handleSearchSubmit}>
          <div className="admin-filter-group">
            <input
              type="text"
              className="admin-filter-input"
              placeholder="Search by product code or name..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
            <button type="submit" className="btn btn-primary btn-sm">
              <FaSearch />
            </button>
            {search && (
              <button type="button" className="btn btn-secondary btn-sm" onClick={handleClearSearch}>
                Clear
              </button>
            )}
          </div>

          <div className="admin-filter-group">
            <select
              className="admin-filter-select"
              value={categoryFilter}
              onChange={(e) => { setCategoryFilter(e.target.value); setPage(0); }}
            >
              <option value="">All Categories</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
            {categoryFilter && (
              <button type="button" className="btn btn-secondary btn-sm" onClick={handleClearCategory}>
                Clear
              </button>
            )}
          </div>

          <div className="admin-filter-group">
            <select
              className="admin-filter-select"
              value={activeFilter}
              onChange={(e) => { setActiveFilter(e.target.value); setPage(0); }}
            >
              <option value="">All Status</option>
              <option value="active">Active Only</option>
              <option value="inactive">Inactive Only</option>
            </select>
          </div>

          <div className="admin-filter-group">
            <select
              className="admin-filter-select"
              value={featuredFilter}
              onChange={(e) => { setFeaturedFilter(e.target.value); setPage(0); }}
            >
              <option value="">All Products</option>
              <option value="featured">Featured Only</option>
            </select>
          </div>
        </form>

        <div className="admin-result-count">
          {total} product{total !== 1 ? 's' : ''} found
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading products...</div>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Product Code</th>
                <th>Name</th>
                <th>Price</th>
                <th>Category</th>
                <th>Variants</th>
                <th>Featured</th>
                <th>In Stock</th>
                <th>Active</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.length === 0 ? (
                <tr>
                  <td colSpan="10" className="table-empty">No products found</td>
                </tr>
              ) : (
                products.map((product, index) => (
                  <tr key={product.id}>
                    <td>{page * PAGE_SIZE + index + 1}</td>
                    <td>{product.product_code}</td>
                    <td>{product.name}</td>
                    <td>{product.price_range ? (parseFloat(product.price_range.min) === parseFloat(product.price_range.max) ? `৳${parseFloat(product.price_range.min).toLocaleString()}` : `৳${parseFloat(product.price_range.min).toLocaleString()} - ৳${parseFloat(product.price_range.max).toLocaleString()}`) : 'N/A'}</td>
                    <td>{product.category_name || product.category_id}</td>
                    <td>
                      <button
                        className="btn btn-sm btn-variants"
                        onClick={() => handleViewVariants(product.id)}
                      >
                        <FaCubes /> {product.total_variants || 0} Variants
                      </button>
                    </td>
                    <td className="text-center">
                      <button
                        className={`btn btn-sm ${product.is_featured ? 'btn-warning' : 'btn-secondary'}`}
                        onClick={() => handleToggleFeatured(product.id, product.is_featured)}
                        disabled={togglingId === product.id}
                        aria-label={product.is_featured ? 'Unmark as featured' : 'Mark as featured'}
                        title={product.is_featured ? 'Featured - click to unmark' : 'Mark as featured'}
                      >
                        {togglingId === product.id ? '...' : product.is_featured ? '★' : '☆'}
                      </button>
                    </td>
                    <td>
                      <span className={`badge ${product.is_in_stock ? 'badge-green' : 'badge-red'}`}>
                        {product.is_in_stock ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${product.is_active ? 'badge-green' : 'badge-red'}`}>
                        {product.is_active ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td>
                      <div className="table-actions">
                        <button
                          className="action-btn action-edit"
                          onClick={() => handleEdit(product.id)}
                          aria-label={`Edit ${product.name}`}
                        >
                          <FaEdit />
                        </button>
                        <button
                          className="action-btn action-delete"
                          onClick={() => handleDelete(product.id, product.name)}
                          aria-label={`Delete ${product.name}`}
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

      {/* Pagination */}
      {!loading && (
        <Pagination
          page={page}
          total={total}
          pageSize={PAGE_SIZE}
          onPageChange={handlePageChange}
          loading={loading}
        />
      )}

      <Modal
        isOpen={deleteModal.show}
        onClose={() => setDeleteModal({ show: false, id: null, name: '' })}
        onConfirm={confirmDelete}
        title="Delete Product"
        message={`Are you sure you want to delete "${deleteModal.name}"?`}
        confirmText="Delete"
        type="danger"
      />
    </div>
  );
}

export default AdminProducts;
