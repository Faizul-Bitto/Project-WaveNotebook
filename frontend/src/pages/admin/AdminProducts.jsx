import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaPlus, FaEdit, FaTrash } from 'react-icons/fa';
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
                <th>ID</th>
                <th>Image</th>
                <th>Product Code</th>
                <th>Name</th>
                <th>Price</th>
                <th>Category</th>
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
                products.map((product) => (
                  <tr key={product.id}>
                    <td>{product.id}</td>
                    <td>
                      {product.image_url ? (
                        <img src={product.image_url} alt={product.name} className="table-image" />
                      ) : (
                        <img src="https://placehold.co/60x40?text=No+Image" alt="No Image" className="table-image" />
                      )}
                    </td>
                    <td>{product.product_code}</td>
                    <td>{product.name}</td>
                    <td>৳{parseFloat(product.base_price).toLocaleString()}</td>
                    <td>{product.category_name || product.category_id}</td>
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
