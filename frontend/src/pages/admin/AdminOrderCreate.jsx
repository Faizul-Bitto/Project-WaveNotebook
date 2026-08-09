import { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { FaArrowLeft, FaPlus, FaTrash, FaSave } from 'react-icons/fa';
import { getDistricts } from '../../api/services';
import { adminGetProducts, adminGetProduct, adminCreateOrder, adminUpdateOrder, adminGetOrder } from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';

function AdminOrderCreate() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditing = Boolean(id);
  const { addToast } = useToast();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(Boolean(id));
  const [districts, setDistricts] = useState([]);
  const [customer, setCustomer] = useState({ full_name: '', phone_number: '', district: '', thana: '', note: '', address: '' });
  const [items, setItems] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState('');
  const [saving, setSaving] = useState(false);
  const [productCache, setProductCache] = useState({});

  // Load products and districts
  useEffect(() => {
    const loadData = async () => {
      try {
        const [pData, dData] = await Promise.all([
          adminGetProducts({ limit: 100, is_active: true }),
          getDistricts(),
        ]);
        setProducts(pData.products || []);
        setDistricts(dData.districts || []);
      } catch {
        addToast('Failed to load data.', 'error');
      }
    };
    loadData();
  }, []);

  // Load full product detail (with attributes/options) when needed
  const loadProductDetail = async (pid) => {
    if (productCache[pid]) return productCache[pid];
    try {
      const data = await adminGetProduct(pid);
      const prod = data.product;
      setProductCache((prev) => ({ ...prev, [pid]: prod }));
      return prod;
    } catch {
      return null;
    }
  };

  // Load existing order when editing - show items immediately
  useEffect(() => {
    if (!isEditing) return;
    const loadOrder = async () => {
      try {
        setLoading(true);
        const data = await adminGetOrder(id);
        const order = data.order;
        setCustomer({
          full_name: order.full_name || '',
          phone_number: order.phone_number || '',
          district: order.district || '',
          thana: order.thana || '',
          note: order.note || '',
          address: order.address || '',
        });

        // Build items immediately from order data
        const baseItems = (order.items || []).map((item) => {
          let selected_options = {};
          if (item.selected_attributes) {
            try { selected_options = JSON.parse(item.selected_attributes); } catch {}
          }
          return {
            product_id: item.product_id,
            product_name: item.product_name || `Product #${item.product_id}`,
            quantity: item.quantity,
            selected_options,
            attributes: [],
          };
        });
        setItems(baseItems);

        // Then asynchronously load product attributes for each item
        for (const item of baseItems) {
          try {
            const detail = await loadProductDetail(item.product_id);
            if (detail?.attributes) {
              setItems((prev) => prev.map((it) =>
                it.product_id === item.product_id ? { ...it, attributes: detail.attributes } : it
              ));
            }
          } catch {}
        }
      } catch (err) {
        addToast(err.response?.data?.detail || 'Failed to load order.', 'error');
      } finally {
        setLoading(false);
      }
    };
    loadOrder();
  }, [id, isEditing]);

  const handleAddProduct = async () => {
    if (!selectedProductId) return;
    const pid = parseInt(selectedProductId);
    const product = products.find((p) => p.id === pid);
    if (!product) return;

    const detail = await loadProductDetail(pid);
    setItems((prev) => [
      ...prev,
      {
        product_id: pid,
        product_name: product.name,
        quantity: 1,
        selected_options: {},
        attributes: detail?.attributes || [],
      },
    ]);
    setSelectedProductId('');
  };

  const handleQuantityChange = (index, qty) => {
    setItems((prev) => prev.map((it, i) => (i === index ? { ...it, quantity: Math.max(1, qty) } : it)));
  };

  const handleOptionChange = (index, attrId, optionId) => {
    setItems((prev) => prev.map((it, i) => {
      if (i !== index) return it;
      const selected_options = { ...it.selected_options, [attrId]: optionId };
      return { ...it, selected_options };
    }));
  };

  const handleRemoveItem = (index) => {
    setItems((prev) => prev.filter((_, i) => i !== index));
  };

  const buildPayload = () => {
    const payloadItems = items.map((it) => {
      const selected_attributes = Object.keys(it.selected_options).length > 0
        ? JSON.stringify(it.selected_options)
        : null;
      return {
        product_id: it.product_id,
        quantity: it.quantity,
        selected_attributes,
      };
    });
    return {
      full_name: customer.full_name,
      phone_number: customer.phone_number,
      district: customer.district,
      thana: customer.thana,
      note: customer.note || null,
      address: customer.address,
      items: payloadItems,
    };
  };

   const handleSubmit = async (e) => {
    e.preventDefault();

    if (!customer.full_name.trim()) return addToast('Enter customer name.', 'error');
    if (!customer.phone_number.trim() || customer.phone_number.trim().length < 11) return addToast('Enter a valid 11-digit phone number.', 'error');
    if (!customer.district) return addToast('Select a district.', 'error');
    if (!customer.address.trim()) return addToast('Enter the address.', 'error');
    if (items.length === 0) return addToast('Add at least one product.', 'error');

    try {
      setSaving(true);
      const payload = buildPayload();
      const result = isEditing
        ? await adminUpdateOrder(id, payload)
        : await adminCreateOrder(payload);
      navigate(`/admin/orders/${result.order.id}`);
      addToast('Order saved successfully!', 'success');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to save order.', 'error');
    } finally {
      setSaving(false);
    }
  };

  const calculateItemTotal = (item) => {
    let unit = parseFloat(products.find((p) => p.id === item.product_id)?.base_price || '0');
    item.attributes?.forEach((attr) => {
      const optId = item.selected_options[attr.id];
      if (optId) {
        const option = attr.options.find((o) => o.id === optId);
        if (option) unit += parseFloat(option.additional_price || '0');
      }
    });
    return unit * item.quantity;
  };

  const totalPrice = items.reduce((sum, it) => sum + calculateItemTotal(it), 0);

  if (loading) return <div className="loading">Loading order...</div>;

  return (
    <div className="admin-page order-create-page">
      <div className="admin-page-header">
        <h2>{isEditing ? 'Edit Order' : 'Create Order'}</h2>
        <div className="header-actions">
          <Link to="/admin/orders" className="btn btn-secondary">
            <FaArrowLeft /> Back
          </Link>
        </div>
       </div>

      <form onSubmit={handleSubmit}>
        {/* Customer Info */}
        <div className="order-detail-card">
          <h3>Customer Information</h3>
          <div className="order-detail-grid">
            <div className="form-group">
              <label>Full Name *</label>
              <input type="text" value={customer.full_name} onChange={(e) => setCustomer({ ...customer, full_name: e.target.value })} placeholder="Customer name" />
            </div>
            <div className="form-group">
              <label>Phone Number *</label>
              <input type="tel" value={customer.phone_number} onChange={(e) => setCustomer({ ...customer, phone_number: e.target.value })} placeholder="01XXXXXXXXX" />
            </div>
            <div className="form-group">
              <label>District *</label>
              <select value={customer.district} onChange={(e) => setCustomer({ ...customer, district: e.target.value })}>
                <option value="">Select District</option>
                {districts.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Thana / Upazila *</label>
              <input type="text" value={customer.thana} onChange={(e) => setCustomer({ ...customer, thana: e.target.value })} placeholder="Enter thana / upazila" />
            </div>
          </div>
          <div className="form-group">
            <label>Full Address *</label>
            <textarea value={customer.address} onChange={(e) => setCustomer({ ...customer, address: e.target.value })} rows="2" placeholder="House, Road, Area" />
          </div>
          <div className="form-group">
            <label>Note (optional)</label>
            <textarea value={customer.note} onChange={(e) => setCustomer({ ...customer, note: e.target.value })} rows="2" placeholder="Add a short note (optional)" />
          </div>
        </div>

        {/* Add Products */}
        <div className="order-detail-card">
          <h3>Add Products</h3>
          <div className="product-add-row">
            <select value={selectedProductId} onChange={(e) => setSelectedProductId(e.target.value)}>
              <option value="">Select a product...</option>
              {products.map((p) => <option key={p.id} value={p.id}>{p.name} (৳{parseFloat(p.base_price).toLocaleString()})</option>)}
            </select>
            <button type="button" className="btn btn-primary" onClick={handleAddProduct}>
              <FaPlus /> Add Product
            </button>
          </div>

          {items.length > 0 ? (
            <div className="order-items-builder">
              {items.map((item, index) => (
                <div className="order-item-builder" key={index}>
                  <div className="item-builder-header">
                    <strong>{item.product_name}</strong>
                    <div className="qty-row">
                      <button type="button" onClick={() => handleQuantityChange(index, item.quantity - 1)}>-</button>
                      <span>{item.quantity}</span>
                      <button type="button" onClick={() => handleQuantityChange(index, item.quantity + 1)}>+</button>
                    </div>
                    <button type="button" className="btn-remove-item" onClick={() => handleRemoveItem(index)}>
                      <FaTrash />
                    </button>
                  </div>
                  {item.attributes?.length > 0 && (
                    <div className="item-options">
                      {item.attributes.map((attr) => (
                        <div className="option-group" key={attr.id}>
                          <span className="option-name">{attr.name}:</span>
                          <select
                            value={item.selected_options[attr.id] || ''}
                            onChange={(e) => handleOptionChange(index, attr.id, parseInt(e.target.value))}
                          >
                            <option value="">Select...</option>
                            {attr.options.map((opt) => (
                              <option key={opt.id} value={opt.id}>
                                {opt.value}{parseFloat(opt.additional_price) > 0 ? ` (+৳${parseFloat(opt.additional_price)})` : ''}
                              </option>
                            ))}
                          </select>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="item-builder-total">৳{calculateItemTotal(item).toLocaleString()}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-items-hint">No products added yet. Select a product above.</p>
          )}
        </div>

        {/* Summary & Submit */}
        <div className="order-detail-card">
          <h3>Order Total</h3>
          <p className="total-price">৳{totalPrice.toLocaleString()}</p>
          <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>
            <FaSave /> {saving ? 'Saving...' : isEditing ? 'Update Order' : 'Create Order'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default AdminOrderCreate;