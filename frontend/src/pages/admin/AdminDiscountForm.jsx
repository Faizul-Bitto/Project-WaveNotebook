import { useEffect, useState, useRef } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { FaArrowLeft, FaPlus, FaTrash, FaTimes, FaSearch, FaCheck } from 'react-icons/fa';
import {
  adminGetDiscount,
  adminCreateDiscount,
  adminUpdateDiscount,
  adminGetProducts,
} from '../../api/adminServices';
import { getProducts, getCategories } from '../../api/services';
import { useToast } from '../../context/ToastContext';
import ProductCategoryPicker from '../../components/ProductCategoryPicker';

const DISCOUNT_TYPES = [
  { value: 'percentage', label: 'Percentage Discount' },
  { value: 'flat', label: 'Flat Discount' },
  { value: 'bundle', label: 'Bundle Discount' },
  { value: 'bogo', label: 'BOGO (Buy X Get Y)' },
  { value: 'free_shipping', label: 'Free Shipping' },
  { value: 'spend_based', label: 'Spend-based Discount' },
];

function AdminDiscountForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditing = Boolean(id);
  const { addToast } = useToast();
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(Boolean(id));
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [productSearch, setProductSearch] = useState('');
  const [showProductPicker, setShowProductPicker] = useState(false);
  const productPickerRef = useRef(null);

  const [formData, setFormData] = useState({
    name: '',
    type: 'percentage',
    value_type: 'percentage',
    value: '',
    max_discount_cap: '',
    scope_type: 'product',
    scope_ids: [],
    bundle_type: 'quantity',
    bundle_slabs: [{ min_quantity: 3, value_type: 'percentage', value: '10' }],
    required_products: '',
    free_shipping: false,
    bogo: {
      product_ids: [],
      buy_quantity: 1,
      get_quantity: 1,
      get_discount_percent: 100,
    },
    spend_based: {
      scope_type: 'storewide',
      scope_id: '',
      slabs: [{ min_spend_amount: 1000, value_type: 'percentage', value: '10' }],
    },
    start_date: '',
    end_date: '',
    status: 'active',
  });

  useEffect(() => {
    const loadData = async () => {
      try {
        const [prodData, catData] = await Promise.all([
          getProducts({ limit: 500, is_active: true }),
          getCategories(),
        ]);
        setProducts(prodData.products || []);
        setCategories(catData.categories || []);
      } catch {
        console.error('Failed to load products/categories for picker');
      }
    };
    loadData();
  }, []);

  useEffect(() => {
    if (isEditing) {
      const loadDiscount = async () => {
        try {
          setLoading(true);
          const data = await adminGetDiscount(id);
          const d = data.discount;
          const scope = d.scopes && d.scopes.length > 0 ? d.scopes[0] : null;

          const base = {
            name: d.name || '',
            type: d.type || 'percentage',
            value_type: d.value_type || 'percentage',
            value: d.value || '',
            max_discount_cap: d.max_discount_cap || '',
            scope_type: d.scopes && d.scopes.length > 0 ? d.scopes[0].scope_type : 'product',
            scope_ids: (d.scopes || []).map(s => s.scope_id),
            bundle_type: d.bundle_rule?.bundle_type || 'quantity',
            bundle_slabs: [],
            required_products: '',
            free_shipping: d.free_shipping || d.bundle_rule?.free_shipping || false,
            bogo: {
              product_ids: d.bogo_rule?.product_ids || (d.bogo_rule?.product_id ? [d.bogo_rule.product_id] : []),
              buy_quantity: d.bogo_rule?.buy_quantity || 1,
              get_quantity: d.bogo_rule?.get_quantity || 1,
              get_discount_percent: d.bogo_rule?.get_discount_percent || 100,
            },
            spend_based: {
              scope_type: d.spend_based_rule?.scope_type || 'storewide',
              scope_id: d.spend_based_rule?.scope_id || '',
              slabs: d.spend_based_rule?.slabs?.map(s => ({
                min_spend_amount: s.min_spend_amount,
                value_type: s.value_type,
                value: String(s.value),
              })) || [{ min_spend_amount: 1000, value_type: 'percentage', value: '10' }],
            },
            start_date: d.start_date ? d.start_date.slice(0, 16) : '',
            end_date: d.end_date ? d.end_date.slice(0, 16) : '',
            status: d.status || 'active',
          };

          if (d.bundle_rule && d.bundle_rule.required_products) {
            try {
              base.required_products = JSON.stringify(d.bundle_rule.required_products);
            } catch {
              base.required_products = '';
            }
          }

          if (d.bundle_rule && d.bundle_rule.slabs && d.bundle_rule.slabs.length > 0) {
            base.bundle_slabs = d.bundle_rule.slabs.map(s => ({
              min_quantity: s.min_quantity,
              value_type: s.value_type,
              value: String(s.value),
            }));
          } else if (d.type === 'bundle' || d.type === 'percentage' || d.type === 'flat') {
            base.bundle_slabs = [{ min_quantity: 3, value_type: 'percentage', value: '10' }];
          }

          setFormData(base);
        } catch (err) {
          addToast(err.response?.data?.detail || 'Failed to load discount.', 'error');
          navigate('/admin/discounts');
        } finally {
          setLoading(false);
        }
      };
      loadDiscount();
    }
  }, [id, isEditing, navigate, addToast]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => {
      const updates = {
        ...prev,
        [name]: type === 'checkbox' ? checked : value,
      };
      if (name === 'scope_type') {
        updates.scope_ids = [];
      }
      return updates;
    });
  };

  const handleBogoChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      bogo: {
        ...prev.bogo,
        [name]: type === 'checkbox' ? checked : type === 'number' ? parseInt(value) || 0 : value,
      },
    }));
  };

  const handleSpendBasedChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => {
      const updatedSpendBased = {
        ...prev.spend_based,
        [name]: type === 'checkbox' ? checked : type === 'number' ? parseInt(value) || 0 : value,
      };
      if (name === 'scope_type' && value === 'storewide') {
        updatedSpendBased.scope_id = '';
      }
      return {
        ...prev,
        spend_based: updatedSpendBased,
      };
    });
  };

  const addSpendSlab = () => {
    setFormData(prev => ({
      ...prev,
      spend_based: {
        ...prev.spend_based,
        slabs: [...prev.spend_based.slabs, { min_spend_amount: 1000, value_type: 'percentage', value: '10' }],
      },
    }));
  };

  const removeSpendSlab = (idx) => {
    setFormData(prev => ({
      ...prev,
      spend_based: {
        ...prev.spend_based,
        slabs: prev.spend_based.slabs.filter((_, i) => i !== idx),
      },
    }));
  };

  const updateSpendSlab = (idx, field, val) => {
    setFormData(prev => ({
      ...prev,
      spend_based: {
        ...prev.spend_based,
        slabs: prev.spend_based.slabs.map((slab, i) =>
          i === idx ? { ...slab, [field]: field === 'min_spend_amount' ? parseFloat(val) || 0 : val } : slab
        ),
      },
    }));
  };

  const addSlab = () => {
    setFormData(prev => ({
      ...prev,
      bundle_slabs: [...prev.bundle_slabs, { min_quantity: 1, value_type: 'percentage', value: '5' }],
    }));
  };

  const removeSlab = (idx) => {
    setFormData(prev => ({
      ...prev,
      bundle_slabs: prev.bundle_slabs.filter((_, i) => i !== idx),
    }));
  };

  const updateSlab = (idx, field, val) => {
    setFormData(prev => ({
      ...prev,
      bundle_slabs: prev.bundle_slabs.map((slab, i) =>
        i === idx ? { ...slab, [field]: field === 'min_quantity' ? parseInt(val) || 1 : val } : slab
      ),
    }));
  };

  const toggleComboProduct = (productId) => {
    setFormData(prev => {
      let current = [];
      try {
        current = JSON.parse(prev.required_products || '[]');
      } catch {
        current = [];
      }
      if (current.includes(productId)) {
        current = current.filter(id => id !== productId);
      } else {
        current = [...current, productId];
      }
      return { ...prev, required_products: JSON.stringify(current) };
    });
  };

  const getSelectedComboProducts = () => {
    try {
      return JSON.parse(formData.required_products || '[]');
    } catch {
      return [];
    }
  };

  const selectedComboIds = getSelectedComboProducts();
  const filteredProducts = productSearch
    ? products.filter(p => p.name.toLowerCase().includes(productSearch.toLowerCase()))
    : products.slice(0, 20);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);

      if (!formData.name.trim()) {
        addToast('Discount name is required.', 'error');
        return;
      }
      if (!formData.start_date) {
        addToast('Start date is required.', 'error');
        return;
      }
      if (formData.end_date && formData.end_date <= formData.start_date) {
        addToast('End date must be after start date.', 'error');
        return;
      }
      if (formData.type === 'bogo') {
        if (!formData.bogo.product_ids || formData.bogo.product_ids.length === 0) {
          addToast('Please select at least one product for BOGO discount from the Products & Categories panel.', 'error');
          return;
        }
      }

      const payload = {
        name: formData.name,
        type: formData.type,
        status: formData.status,
        start_date: new Date(formData.start_date).toISOString(),
        end_date: formData.end_date ? new Date(formData.end_date).toISOString() : null,
      };

      if (formData.type === 'percentage' || formData.type === 'flat') {
        payload.value_type = formData.value_type;
        payload.value = parseFloat(formData.value);
        payload.max_discount_cap = formData.max_discount_cap ? parseFloat(formData.max_discount_cap) : null;
        payload.scope_type = formData.scope_type;
        payload.scope_ids = formData.scope_ids && formData.scope_ids.length > 0 ? formData.scope_ids : null;
      }

      payload.free_shipping = formData.free_shipping;

      if (formData.type === 'free_shipping') {
        payload.scope_type = formData.scope_type;
        payload.scope_ids = formData.scope_ids && formData.scope_ids.length > 0 ? formData.scope_ids : null;
      }

      if (formData.type === 'bundle') {
        payload.bundle_type = formData.bundle_type;

        if (formData.bundle_type === 'quantity') {
          payload.bundle_slabs = formData.bundle_slabs.map(s => ({
            min_quantity: s.min_quantity,
            value_type: s.value_type,
            value: parseFloat(s.value),
          }));
          payload.scope_type = formData.scope_type;
          payload.scope_ids = formData.scope_ids && formData.scope_ids.length > 0 ? formData.scope_ids : null;
        } else if (formData.bundle_type === 'combo') {
          payload.required_products = formData.required_products;
          payload.bundle_slabs = formData.bundle_slabs.filter(s => parseFloat(s.value) > 0).map(s => ({
            min_quantity: 1,
            value_type: s.value_type,
            value: parseFloat(s.value),
          }));
        }
      }

      if (formData.type === 'bogo') {
        payload.bogo = {
          product_id: null,
          product_ids: formData.bogo.product_ids && formData.bogo.product_ids.length > 0
            ? formData.bogo.product_ids.map(id => parseInt(id))
            : null,
          buy_quantity: formData.bogo.buy_quantity,
          get_quantity: formData.bogo.get_quantity,
          get_discount_percent: parseFloat(formData.bogo.get_discount_percent),
        };
      }

      if (formData.type === 'spend_based' && formData.spend_based) {
        payload.spend_based = {
          scope_type: formData.spend_based.scope_type || 'storewide',
          scope_id: formData.spend_based.scope_id ? parseInt(formData.spend_based.scope_id) : null,
          slabs: formData.spend_based.slabs.map(s => ({
            min_spend_amount: parseFloat(s.min_spend_amount),
            value_type: s.value_type,
            value: parseFloat(s.value),
          })),
        };
      }

      if (isEditing) {
        await adminUpdateDiscount(id, payload);
        addToast('Discount updated successfully!', 'success');
      } else {
        await adminCreateDiscount(payload);
        addToast('Discount created successfully!', 'success');
      }

      navigate('/admin/discounts');
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        addToast(detail.map(d => d.msg).join(', '), 'error');
      } else {
        addToast(detail || 'Failed to save discount.', 'error');
      }
    } finally {
      setSaving(false);
    }
  };

  const isBundleQuantity = formData.type === 'bundle' && formData.bundle_type === 'quantity';
  const isBundleCombo = formData.type === 'bundle' && formData.bundle_type === 'combo';
  const isPriceDiscount = formData.type === 'percentage' || formData.type === 'flat';
  const isBogo = formData.type === 'bogo';
  const isFreeShipping = formData.type === 'free_shipping';
  const isSpendBased = formData.type === 'spend_based';

  const sidebarScopeIds = isSpendBased
    ? (formData.spend_based.scope_id ? [formData.spend_based.scope_id] : [])
    : formData.scope_ids;

  const showSidebarPicker = !isSpendBased || formData.spend_based.scope_type !== 'storewide';

  const handleSidebarChange = (ids) => {
    if (isBogo) {
      setFormData(prev => ({
        ...prev,
        bogo: {
          ...prev.bogo,
          product_ids: ids,
        },
      }));
    } else if (isSpendBased) {
      setFormData(prev => ({
        ...prev,
        spend_based: {
          ...prev.spend_based,
          scope_id: ids.length > 0 ? ids[ids.length - 1] : '',
        },
      }));
    } else if (isBundleCombo) {
      setFormData(prev => ({ ...prev, required_products: JSON.stringify(ids) }));
    } else {
      setFormData(prev => ({ ...prev, scope_ids: ids }));
    }
  };

  if (loading) {
    return <div className="loading">Loading discount...</div>;
  }

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <div>
          <button className="btn btn-outline btn-sm" onClick={() => navigate('/admin/discounts')}>
            <FaArrowLeft /> Back
          </button>
        </div>
        <h2>{isEditing ? 'Edit Discount' : 'Create Discount'}</h2>
      </div>

      <form className="admin-form discount-form" onSubmit={handleSubmit}>
        <div className="discount-layout">
          <div className="discount-main">
            <h3>Basic Information</h3>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="name">Discount Name *</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  placeholder="e.g., Summer Sale 20% Off"
                />
              </div>
              <div className="form-group">
                <label htmlFor="type">Discount Type *</label>
                <select id="type" name="type" value={formData.type} onChange={handleChange}>
                  {DISCOUNT_TYPES.map(t => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="start_date">Start Date *</label>
                <input
                  type="datetime-local"
                  id="start_date"
                  name="start_date"
                  value={formData.start_date}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="end_date">End Date (Optional)</label>
                <input
                  type="datetime-local"
                  id="end_date"
                  name="end_date"
                  value={formData.end_date}
                  onChange={handleChange}
                />
                <small className="form-help">Leave empty for unlimited time</small>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="status">Status</label>
              <select id="status" name="status" value={formData.status} onChange={handleChange}>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>

            {/* Percentage / Flat fields */}
            {isPriceDiscount && (
              <div className="discount-section">
                <h3>Discount Value</h3>
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="value_type">Value Type *</label>
                    <select id="value_type" name="value_type" value={formData.value_type} onChange={handleChange}>
                      <option value="percentage">Percentage (%)</option>
                      <option value="flat">Flat Amount (৳)</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label htmlFor="value">Value *</label>
                    <input
                      type="number"
                      id="value"
                      name="value"
                      value={formData.value}
                      onChange={handleChange}
                      required
                      min="0"
                      step={formData.value_type === 'percentage' ? '1' : '0.01'}
                      placeholder={formData.value_type === 'percentage' ? 'e.g., 20 for 20%' : 'e.g., 50 for ৳50 off'}
                    />
                  </div>
                </div>

                {formData.value_type === 'percentage' && (
                  <div className="form-group">
                    <label htmlFor="max_discount_cap">Max Discount Cap (Optional)</label>
                    <input
                      type="number"
                      id="max_discount_cap"
                      name="max_discount_cap"
                      value={formData.max_discount_cap}
                      onChange={handleChange}
                      min="0"
                      step="0.01"
                      placeholder="e.g., 500 for max ৳500 off"
                    />
                    <small className="form-help">Maximum discount amount for percentage discounts</small>
                  </div>
                )}
              </div>
            )}

            {/* Bundle fields */}
            {formData.type === 'bundle' && (
              <div className="discount-section">
                <h3>Bundle Configuration</h3>
                <div className="form-group">
                  <label htmlFor="bundle_type">Bundle Type *</label>
                  <select id="bundle_type" name="bundle_type" value={formData.bundle_type} onChange={handleChange}>
                    <option value="quantity">Quantity-Based Bundle</option>
                    <option value="combo">Combo Bundle</option>
                  </select>
                </div>

                {isBundleQuantity && (
                  <div className="discount-section">
                    <div className="form-group">
                      <label>Bundle Slabs / Tiers</label>
                      <div className="slabs-list">
                        {formData.bundle_slabs.map((slab, idx) => (
                          <div key={idx} className="slab-row">
                            <span className="slab-label">Slab {idx + 1}:</span>
                            <input
                              type="number"
                              value={slab.min_quantity}
                              onChange={(e) => updateSlab(idx, 'min_quantity', e.target.value)}
                              min="1"
                              placeholder="Min Qty"
                              className="slab-input slab-input-qty"
                            />
                            <select
                              value={slab.value_type}
                              onChange={(e) => updateSlab(idx, 'value_type', e.target.value)}
                              className="slab-select"
                            >
                              <option value="percentage">%</option>
                              <option value="flat">৳</option>
                            </select>
                            <input
                              type="number"
                              value={slab.value}
                              onChange={(e) => updateSlab(idx, 'value', e.target.value)}
                              min="0"
                              step={slab.value_type === 'percentage' ? '1' : '0.01'}
                              placeholder="Value"
                              className="slab-input"
                            />
                            {formData.bundle_slabs.length > 1 && (
                              <button
                                type="button"
                                className="btn btn-danger btn-sm"
                                onClick={() => removeSlab(idx)}
                              >
                                <FaTrash />
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                      <button type="button" className="btn btn-outline btn-sm add-slab-btn" onClick={addSlab}>
                        <FaPlus /> Add Slab
                      </button>
                    </div>
                  </div>
                )}

                {isBundleCombo && (
                  <div className="discount-section">
                    <p className="form-help" style={{ marginBottom: 12 }}>
                      Select the products to include in this combo bundle from the <strong>Products & Categories</strong> panel on the right.
                    </p>
                    <div className="form-group">
                      <label htmlFor="bundle_combo_value">Combo Discount Value</label>
                        <div className="form-row">
                          <select
                            value={formData.bundle_slabs[0]?.value_type || 'percentage'}
                            onChange={(e) => setFormData(prev => ({
                              ...prev,
                              bundle_slabs: [{ ...prev.bundle_slabs[0], value_type: e.target.value }],
                            }))}
                            className="slab-select"
                          >
                            <option value="percentage">Percentage (%)</option>
                            <option value="flat">Flat (৳)</option>
                          </select>
                          <input
                            type="number"
                            value={formData.bundle_slabs[0]?.value || ''}
                            onChange={(e) => setFormData(prev => ({
                              ...prev,
                              bundle_slabs: [{ ...prev.bundle_slabs[0], value: e.target.value }],
                            }))}
                            min="0"
                            step="0.01"
                            placeholder="Discount value"
                          />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Free Shipping add-on checkbox for non-free-shipping discount types */}
            {!isFreeShipping && (
              <div className="form-checkbox">
                <label>
                  <input
                    type="checkbox"
                    name="free_shipping"
                    checked={formData.free_shipping}
                    onChange={handleChange}
                  />
                  Include Free Shipping with this discount
                </label>
              </div>
            )}

            {/* BOGO fields */}
            {isBogo && (
              <div className="discount-section">
                <h3>BOGO Configuration</h3>
                <p className="form-help" style={{ marginBottom: 12 }}>
                  Select products from the <strong>Products & Categories</strong> panel on the right. The same buy/get configuration below will apply to all selected products.
                </p>
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="bogo_buy">Buy Quantity *</label>
                    <input
                      type="number"
                      id="bogo_buy"
                      name="buy_quantity"
                      value={formData.bogo.buy_quantity}
                      onChange={handleBogoChange}
                      required
                      min="1"
                    />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="bogo_get">Get Quantity *</label>
                    <input
                      type="number"
                      id="bogo_get"
                      name="get_quantity"
                      value={formData.bogo.get_quantity}
                      onChange={handleBogoChange}
                      required
                      min="1"
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="bogo_discount">Get Discount % *</label>
                    <input
                      type="number"
                      id="bogo_discount"
                      name="get_discount_percent"
                      value={formData.bogo.get_discount_percent}
                      onChange={handleBogoChange}
                      required
                      min="0"
                      max="100"
                    />
                     <small className="form-help">100% = fully free</small>
                     </div>
                    </div>
                  </div>
              )}

            {/* Free Shipping fields */}
            {isFreeShipping && (
              <div className="discount-section">
                <h3>Free Shipping Configuration</h3>
                <p className="form-help">Free shipping discounts are applied automatically based on delivery zone and district. No additional configuration needed.</p>
              </div>
            )}

            {/* Spend-based fields */}
            {formData.type === 'spend_based' && (
              <div className="discount-section">
                <h3>Spend-based Configuration</h3>
                <div className="form-group">
                  <label htmlFor="spend_scope_type">Apply To</label>
                  <select
                    id="spend_scope_type"
                    name="scope_type"
                    value={formData.spend_based.scope_type}
                    onChange={handleSpendBasedChange}
                  >
                    <option value="storewide">Storewide</option>
                    <option value="category">Specific Category(ies)</option>
                    <option value="product">Specific Product(s)</option>
                  </select>
                </div>
                {formData.spend_based.scope_type !== 'storewide' && (
                  <div className="form-group">
                    <p className="form-help" style={{ marginTop: 8 }}>
                      Select {formData.spend_based.scope_type === 'category' ? 'categories' : 'products'} from the <strong>Products & Categories</strong> panel on the right.
                    </p>
                  </div>
                )}
                <div className="form-group">
                  <label>Spend Slabs / Tiers</label>
                  <div className="slabs-list">
                    {formData.spend_based.slabs.map((slab, idx) => (
                      <div key={idx} className="slab-row">
                        <span className="slab-label">Slab {idx + 1}:</span>
                        <input
                          type="number"
                          value={slab.min_spend_amount}
                          onChange={(e) => updateSpendSlab(idx, 'min_spend_amount', e.target.value)}
                          min="0"
                          placeholder="Min Spend"
                          className="slab-input slab-input-qty"
                        />
                        <select
                          value={slab.value_type}
                          onChange={(e) => updateSpendSlab(idx, 'value_type', e.target.value)}
                          className="slab-select"
                        >
                          <option value="percentage">%</option>
                          <option value="flat">৳</option>
                        </select>
                        <input
                          type="number"
                          value={slab.value}
                          onChange={(e) => updateSpendSlab(idx, 'value', e.target.value)}
                          min="0"
                          step={slab.value_type === 'percentage' ? '1' : '0.01'}
                          placeholder="Value"
                          className="slab-input"
                        />
                        {formData.spend_based.slabs.length > 1 && (
                          <button
                            type="button"
                            className="btn btn-danger btn-sm"
                            onClick={() => removeSpendSlab(idx)}
                          >
                            <FaTrash />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                  <button type="button" className="btn btn-outline btn-sm add-slab-btn" onClick={addSpendSlab}>
                    <FaPlus /> Add Slab
                  </button>
                </div>
              </div>
            )}

            <div className="form-actions">
              <button type="button" className="btn btn-outline" onClick={() => navigate('/admin/discounts')}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? 'Saving...' : isEditing ? 'Update Discount' : 'Create Discount'}
              </button>
            </div>
          </div>

          <div className="discount-sidebar">
            <div className="sidebar-sticky">
              <h3>Products & Categories</h3>

               {!showSidebarPicker ? (
                <p className="form-help" style={{ marginBottom: 12 }}>
                  This discount applies storewide. No product or category selection needed.
                </p>
              ) : isSpendBased ? (
                <ProductCategoryPicker
                  scopeType={formData.spend_based.scope_type}
                  scopeIds={sidebarScopeIds}
                  onChange={handleSidebarChange}
                />
              ) : isBogo ? (
                <>
                  <p className="form-help" style={{ marginBottom: 12 }}>
                    Select products to apply this BOGO rule to. The same buy/get configuration will apply to all selected products.
                  </p>
                  <ProductCategoryPicker
                    scopeType="product"
                    scopeIds={formData.bogo.product_ids || []}
                    onChange={handleSidebarChange}
                  />
                </>
              ) : (
                <>
                  <p className="form-help" style={{ marginBottom: 12 }}>
                    Select products or categories for this discount. Use the toggle below to switch between products and categories.
                  </p>
                  <div className="form-group" style={{ marginBottom: 12 }}>
                    <label htmlFor="sidebar_scope_type">Select From</label>
                    <select
                      id="sidebar_scope_type"
                      value={formData.scope_type}
                      onChange={(e) => setFormData(prev => ({ ...prev, scope_type: e.target.value, scope_ids: [] }))}
                    >
                      <option value="product">Products</option>
                      <option value="category">Categories</option>
                    </select>
                  </div>
                  <ProductCategoryPicker
                    scopeType={formData.scope_type}
                    scopeIds={formData.scope_ids}
                    onChange={handleSidebarChange}
                  />
                </>
              )}
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}

export default AdminDiscountForm;
