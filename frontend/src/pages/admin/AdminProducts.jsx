import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaPlus, FaEdit, FaTrash } from 'react-icons/fa';
import {
  adminGetProducts,
  adminDeleteProduct,
} from '../../api/adminServices';

function AdminProducts() {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const data = await adminGetProducts({ limit: 100 });
      setProducts(data.products || []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load products.');
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
        if (mounted) setError(null);
      } catch (err) {
        if (mounted) setError(err.response?.data?.detail || 'Failed to load products.');
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
    if (window.confirm(`Are you sure you want to delete "${name}"?`)) {
      try {
        await adminDeleteProduct(id);
        await loadProducts();
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to delete product.');
      }
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

      {error && <div className="alert alert-error">{error}</div>}

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
                    <td className="table-actions">
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

export default AdminProducts;
