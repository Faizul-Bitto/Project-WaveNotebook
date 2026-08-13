import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaPlus, FaEdit, FaTrash, FaCubes } from 'react-icons/fa';
import {
  adminGetProducts,
  adminDeleteProduct,
} from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';
import Modal from '../../components/Modal';

function AdminProducts() {
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleteModal, setDeleteModal] = useState({ show: false, id: null, name: '' });

  const loadProducts = async () => {
    try {
      setLoading(true);
      const data = await adminGetProducts({ limit: 100 });
      setProducts(data.products || []);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to load products.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await adminGetProducts({ limit: 100 });
        if (mounted) setProducts(data.products || []);
      } catch (err) {
        if (mounted) addToast(err.response?.data?.detail || 'Failed to load products.', 'error');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchData();
    return () => {
      mounted = false;
    };
  }, []);

  const handleDelete = async (id, name) => {
    setDeleteModal({ show: true, id: id, name: name });
  };

  const confirmDelete = async () => {
    const { id } = deleteModal;
    setDeleteModal({ show: false, id: null, name: '' });
    try {
      await adminDeleteProduct(id);
      await loadProducts();
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

  const handleCreate = () => {
    navigate('/admin/products/new');
  };

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h2>Products</h2>
        <button className="btn btn-primary" onClick={handleCreate}>
          <FaPlus /> Add Product
        </button>
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
                <th>In Stock</th>
                <th>Active</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.length === 0 ? (
                <tr>
                  <td colSpan="9" className="table-empty">No products found</td>
                </tr>
              ) : (
                products.map((product, index) => (
                  <tr key={product.id}>
                    <td>{index + 1}</td>
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