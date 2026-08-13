import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FaArrowLeft, FaSave, FaTrash, FaPlus, FaToggleOn, FaToggleOff, FaMagic } from 'react-icons/fa';
import {
  adminGetProductVariants,
  adminBulkUpdateVariants,
  adminDeleteVariant,
  adminGetProduct,
  adminAddNewVariants,
  adminGetAttributes,
  adminGenerateVariantsFromProduct,
} from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';
import Modal from '../../components/Modal';

function AdminProductVariants() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { addToast } = useToast();

  const [product, setProduct] = useState(null);
  const [variants, setVariants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [edits, setEdits] = useState({});
  const [deleteModal, setDeleteModal] = useState({ show: false, id: null, sku: '' });
  const [addVariantsModal, setAddVariantsModal] = useState(false);
  const [attributes, setAttributes] = useState([]);
  const [selectedNewOptions, setSelectedNewOptions] = useState({});

  const loadVariants = async () => {
    try {
      setLoading(true);
      const data = await adminGetProductVariants(id);
      setProduct({ id: data.product_id, name: data.product_name });
      setVariants(data.variants || []);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to load variants.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      try {
        setLoading(true);
        const [variantData, , attrData] = await Promise.all([
          adminGetProductVariants(id),
          adminGetProduct(id),
          adminGetAttributes({ limit: 1000, is_active: true }),
        ]);
        if (mounted) {
          setProduct({ id: variantData.product_id, name: variantData.product_name });
          setVariants(variantData.variants || []);
          setAttributes(attrData.attributes || []);
        }
      } catch (err) {
        if (mounted) addToast(err.response?.data?.detail || 'Failed to load variants.', 'error');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchData();
    return () => { mounted = false; };
  }, [id]);

  const handleEdit = (variantId, field, value) => {
    let normalizedValue = value;
    if (field === 'price' || field === 'buying_price') {
      if (value === '' || value === null || value === undefined) {
        normalizedValue = null;
      } else {
        normalizedValue = parseFloat(value);
        if (isNaN(normalizedValue)) normalizedValue = null;
      }
    }
    setEdits(prev => ({
      ...prev,
      [variantId]: {
        ...prev[variantId],
        [field]: normalizedValue,
      },
    }));
  };

  const handleToggleActive = (variant) => {
    handleEdit(variant.id, 'is_active', !variant.is_active);
  };

  const handleSaveAll = async () => {
    if (Object.keys(edits).length === 0) {
      addToast('No changes to save.', 'info');
      return;
    }

    setSaving(true);
    try {
      const updates = {};
      Object.entries(edits).forEach(([variantId, data]) => {
        updates[variantId] = data;
      });
      const result = await adminBulkUpdateVariants(id, updates);
      addToast(result.message || 'Variants updated successfully!', 'success');
      setEdits({});
      await loadVariants();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to save variants.', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = (variant) => {
    setDeleteModal({ show: true, id: variant.id, sku: variant.sku });
  };

  const confirmDelete = async () => {
    const { id: variantId } = deleteModal;
    setDeleteModal({ show: false, id: null, sku: '' });
    try {
      await adminDeleteVariant(variantId);
      addToast('Variant deleted successfully!', 'success');
      await loadVariants();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to delete variant.', 'error');
    }
  };

  const handleGenerateVariants = async () => {
    setSaving(true);
    try {
      const result = await adminGenerateVariantsFromProduct(id);
      addToast(result.message || 'Variants generated successfully!', 'success');
      await loadVariants();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to generate variants.', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleAddVariants = async () => {
    const newOptionIds = Object.values(selectedNewOptions).flat();
    if (newOptionIds.length === 0) {
      addToast('Please select at least one new option.', 'error');
      return;
    }

    setSaving(true);
    try {
      const result = await adminAddNewVariants(id, newOptionIds);
      addToast(result.message || 'New variants generated!', 'success');
      setAddVariantsModal(false);
      setSelectedNewOptions({});
      await loadVariants();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to generate variants.', 'error');
    } finally {
      setSaving(false);
    }
  };

  const formatAttributes = (attrs) => {
    if (!attrs) return '';
    return Object.entries(attrs)
      .map(([key, value]) => `${key}: ${value}`)
      .join(' | ');
  };

  const getVariantValue = (variant, field) => {
    if (edits[variant.id] && edits[variant.id][field] !== undefined) {
      return edits[variant.id][field];
    }
    return variant[field];
  };

  if (loading) {
    return <div className="loading">Loading variants...</div>;
  }

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <div>
          <h2>Product Variants</h2>
          <p className="variant-product-name">{product?.name}</p>
        </div>
         <div className="header-actions">
          <button className="btn btn-secondary" onClick={() => navigate('/admin/products')}>
            <FaArrowLeft /> Back to Products
          </button>
          <button className="btn btn-warning" onClick={handleGenerateVariants} disabled={saving}>
            <FaMagic /> {saving ? 'Generating...' : 'Generate All Variants'}
          </button>
          {variants.length > 0 && (
            <button className="btn btn-primary" onClick={() => setAddVariantsModal(true)}>
              <FaPlus /> Add Variants
            </button>
          )}
          <button className="btn btn-success" onClick={handleSaveAll} disabled={saving || Object.keys(edits).length === 0}>
            <FaSave /> {saving ? 'Saving...' : 'Save All'}
          </button>
        </div>
      </div>

      {Object.keys(edits).length > 0 && (
        <div className="unsaved-changes-banner">
          {Object.keys(edits).length} variant(s) have unsaved changes. Click "Save All" to apply.
        </div>
      )}

      <div className="admin-table-wrap">
        <table className="admin-table variant-table">
          <thead>
            <tr>
              <th>SKU</th>
              <th>Selected Attributes</th>
              <th>Selling Price (৳)</th>
              <th>Buying Price (৳)</th>
              <th>Profit (৳)</th>
              <th>Stock</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {variants.length === 0 ? (
              <tr>
                <td colSpan="8" className="table-empty">No variants found</td>
              </tr>
            ) : (
              variants.map((variant) => {
                const price = getVariantValue(variant, 'price');
                const buyingPrice = getVariantValue(variant, 'buying_price');
                const stock = getVariantValue(variant, 'stock_quantity');
                const isActive = getVariantValue(variant, 'is_active');

                const priceFilled = price !== null && price !== undefined && price !== '' && Number(price) > 0;
                const buyingFilled = buyingPrice !== null && buyingPrice !== undefined && buyingPrice !== '' && Number(buyingPrice) > 0;

                const profit = priceFilled && buyingFilled
                  ? (parseFloat(price) - parseFloat(buyingPrice)).toFixed(2)
                  : null;

                return (
                  <tr key={variant.id} className={!isActive ? 'variant-inactive' : ''}>
                    <td className="variant-sku">{variant.sku}</td>
                    <td className="variant-attrs">{formatAttributes(variant.selected_attributes)}</td>
                    <td>
                      <input
                        type="number"
                        className={`variant-input ${!priceFilled ? 'variant-input-empty' : ''}`}
                        value={priceFilled ? price : ''}
                        placeholder="Set price"
                        min="0"
                        step="0.01"
                        onChange={(e) => handleEdit(variant.id, 'price', e.target.value)}
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        className={`variant-input ${!buyingFilled ? 'variant-input-empty' : ''}`}
                        value={buyingFilled ? buyingPrice : ''}
                        placeholder="Set buying price"
                        min="0"
                        step="0.01"
                        onChange={(e) => handleEdit(variant.id, 'buying_price', e.target.value)}
                      />
                    </td>
                    <td className={profit !== null && profit < 0 ? 'profit-negative' : ''}>
                      {profit !== null ? `৳${parseFloat(profit).toLocaleString()}` : '—'}
                    </td>
                    <td>
                      <input
                        type="number"
                        className="variant-input variant-stock-input"
                        value={stock ?? 0}
                        min="0"
                        onChange={(e) => handleEdit(variant.id, 'stock_quantity', parseInt(e.target.value) || 0)}
                      />
                    </td>
                    <td>
                      <button
                        className={`status-toggle ${isActive ? 'active' : 'inactive'}`}
                        onClick={() => handleToggleActive(variant)}
                        title={isActive ? 'Active - Click to deactivate' : 'Inactive - Click to activate'}
                      >
                        {isActive ? <FaToggleOn /> : <FaToggleOff />}
                      </button>
                    </td>
                    <td>
                      <div className="table-actions">
                        <button
                          className="action-btn action-delete"
                          onClick={() => handleDelete(variant)}
                          aria-label={`Delete ${variant.sku}`}
                        >
                          <FaTrash />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <Modal
        isOpen={deleteModal.show}
        onClose={() => setDeleteModal({ show: false, id: null, sku: '' })}
        onConfirm={confirmDelete}
        title="Delete Variant"
        message={`Are you sure you want to delete variant "${deleteModal.sku}"?`}
        confirmText="Delete"
        type="danger"
      />

      {addVariantsModal && (
        <div className="modal-overlay" onClick={() => setAddVariantsModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add New Variants</h3>
              <button className="modal-close" onClick={() => setAddVariantsModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <p>Select new attribute options to generate additional variants. New variants will have empty prices that need to be filled.</p>
              {attributes.map(attr => (
                <div key={attr.id} className="add-variant-attr-group">
                  <h4>{attr.name}</h4>
                  <div className="options-grid">
                    {attr.options?.map(opt => (
                      <label key={opt.id} className="option-checkbox">
                        <input
                          type="checkbox"
                          checked={(selectedNewOptions[attr.id] || []).includes(opt.id)}
                          onChange={(e) => {
                            const current = selectedNewOptions[attr.id] || [];
                            const updated = e.target.checked
                              ? [...current, opt.id]
                              : current.filter(id => id !== opt.id);
                            setSelectedNewOptions(prev => ({
                              ...prev,
                              [attr.id]: updated,
                            }));
                          }}
                        />
                        <span>{opt.value}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setAddVariantsModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleAddVariants} disabled={saving}>
                {saving ? 'Generating...' : 'Generate Variants'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminProductVariants;