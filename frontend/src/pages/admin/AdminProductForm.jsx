import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FaTrash, FaImage, FaSave, FaArrowLeft, FaPlus, FaTimes } from 'react-icons/fa';
import {
  adminGetProduct,
  adminCreateProduct,
  adminUpdateProduct,
  adminDeleteProduct,
  adminGetCategories,
  adminGetAttributes,
} from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';
import Modal from '../../components/Modal';

function AdminProductForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditing = Boolean(id);

  const { addToast } = useToast();
  const [categories, setCategories] = useState([]);
  const [attributes, setAttributes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  // Form state - attributes starts empty for better UX
  const [formData, setFormData] = useState({
    category_id: '',
    name: '',
    description: '',
    specifications: '',
    base_price: '',
    is_in_stock: true,
    is_active: true,
    attributes: [],
    files: [],
  });

  // Preview images
  const [previewImages, setPreviewImages] = useState([]);

  // Load categories and attributes
  useEffect(() => {
    const loadData = async () => {
      try {
        const [catData, attrData] = await Promise.all([
          adminGetCategories({ limit: 1000 }),
          adminGetAttributes({ limit: 1000, is_active: true }),
        ]);
        setCategories(catData.categories || []);
        setAttributes(attrData.attributes || []);
      } catch (err) {
        console.error('Failed to load categories/attributes:', err);
      }
    };
    loadData();
  }, []);

  // Load product if editing
  useEffect(() => {
    if (isEditing) {
      const loadProduct = async () => {
        try {
          setLoading(true);
          const data = await adminGetProduct(id);
          const product = data.product;
          
          // Format attributes for form
          const formattedAttributes = (product.attributes || []).map(attr => ({
            attribute_id: attr.id,
            option_ids: attr.options
              .filter(opt => opt.is_selected)
              .map(opt => opt.id)
          }));

          setFormData({
            category_id: product.category_id,
            name: product.name,
            description: product.description || '',
            specifications: product.specifications || '',
            base_price: product.base_price,
            is_in_stock: product.is_in_stock,
            is_active: product.is_active,
            attributes: formattedAttributes,
            files: [],
          });

          // Set preview images
          if (product.files && product.files.length > 0) {
            setPreviewImages(product.files.map(f => ({
              id: f.id,
              url: f.file_url,
              name: f.file_name,
              existing: true,
            })));
          }
        } catch (err) {
          addToast(err.response?.data?.detail || 'Failed to load product.', 'error');
        } finally {
          setLoading(false);
        }
      };
      loadProduct();
    }
  }, [id, isEditing]);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  // Handle attribute selection from dropdown
  const handleAttributeSelect = (attributeId, optionIds) => {
    const attribute = attributes.find(attr => attr.id === attributeId);
    if (!attributeId || !attribute) return;
    
    // Check if this attribute is already added
    const existingIndex = formData.attributes.findIndex(
      attr => attr.attribute_id === attributeId
    );
    
    if (existingIndex >= 0) {
      // Update existing attribute
      setFormData(prev => ({
        ...prev,
        attributes: prev.attributes.map((attr, idx) =>
          idx === existingIndex
            ? { ...attr, attribute_id: attributeId, option_ids: optionIds }
            : attr
        ),
      }));
    } else {
      // Add new attribute
      setFormData(prev => ({
        ...prev,
        attributes: [...prev.attributes, {
          attribute_id: attributeId,
          option_ids: optionIds
        }],
      }));
    }
  };

  // Remove attribute from product
  const removeAttribute = (attributeId) => {
    setFormData(prev => ({
      ...prev,
      attributes: prev.attributes.filter(attr => attr.attribute_id !== attributeId),
    }));
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    const newPreviews = files.map(file => ({
      file,
      url: URL.createObjectURL(file),
      name: file.name,
      existing: false,
    }));
    setPreviewImages(prev => [...prev, ...newPreviews]);
    setFormData(prev => ({
      ...prev,
      files: [...prev.files, ...files],
    }));
  };

  const removeImage = (index) => {
    setPreviewImages(prev => {
      const newPreviews = [...prev];
      if (!newPreviews[index].existing) {
        URL.revokeObjectURL(newPreviews[index].url);
      }
      newPreviews.splice(index, 1);
      return newPreviews;
    });
    setFormData(prev => {
      const newFiles = [...prev.files];
      newFiles.splice(index, 1);
      return { ...prev, files: newFiles };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('category_id', formData.category_id);
      formDataToSend.append('name', formData.name);
      formDataToSend.append('description', formData.description);
      formDataToSend.append('specifications', formData.specifications);
      formDataToSend.append('base_price', formData.base_price);
      formDataToSend.append('is_in_stock', formData.is_in_stock);
      formDataToSend.append('is_active', formData.is_active);
      formDataToSend.append('attributes', JSON.stringify(formData.attributes));

      formData.files.forEach(file => {
        formDataToSend.append('files', file);
      });

      if (isEditing) {
        await adminUpdateProduct(id, formDataToSend);
        addToast('Product updated successfully!', 'success');
      } else {
        await adminCreateProduct(formDataToSend);
        addToast('Product created successfully!', 'success');
      }

      setTimeout(() => navigate('/admin/products'), 1500);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to save product.', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = () => {
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    setShowDeleteModal(false);
    try {
      await adminDeleteProduct(id);
      addToast('Product deleted successfully!', 'success');
      navigate('/admin/products');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to delete product.', 'error');
    }
  };

  if (isEditing && loading) {
    return <div className="loading">Loading product...</div>;
  }

  return (
    <div className="admin-page product-form-page">
      <div className="admin-page-header">
        <h2>{isEditing ? 'Edit Product' : 'Add Product'}</h2>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={() => navigate('/admin/products')}>             
            <FaArrowLeft /> Back to Products
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="product-form">
        <div className="form-grid">
          {/* Left Column - Main Info */}
          <div className="form-section">
            <h3>Basic Information</h3>
            
            <div className="form-group">
              <label htmlFor="category_id">Category *</label>
              <select
                id="category_id"
                name="category_id"
                value={formData.category_id}
                onChange={handleInputChange}
                required
              >
                <option value="">Select Category</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="name">Product Name *</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                required
                placeholder="Enter product name"
              />
            </div>

            <div className="form-group">
              <label htmlFor="base_price">Base Price (৳) *</label>
              <input
                type="number"
                id="base_price"
                name="base_price"
                value={formData.base_price}
                onChange={handleInputChange}
                required
                min="0"
                step="0.01"
                placeholder="0.00"
              />
              <p className="form-hint">Attribute option prices are added on top of base price when customer selects options</p>
            </div>

            <div className="form-group">
              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows="4"
                placeholder="Product description..."
              />
            </div>

            <div className="form-group">
              <label htmlFor="specifications">Specifications</label>
              <textarea
                id="specifications"
                name="specifications"
                value={formData.specifications}
                onChange={handleInputChange}
                rows="4"
                placeholder="Technical specifications..."
              />
            </div>

            <div className="form-group checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="is_in_stock"
                  checked={formData.is_in_stock}
                  onChange={handleInputChange}
                />
                <span>In Stock</span>
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleInputChange}
                />
                <span>Active</span>
              </label>
            </div>
          </div>

          {/* Right Column - Attributes & Images */}
          <div className="form-section">
            <h3>Product Attributes</h3>
            
            {/* Available attributes section */}
            <div className="attribute-selector">
              <h4>Available Attributes</h4>
              <div className="attribute-dropdown-container">
                <select
                  onChange={(e) => {
                    const attrId = e.target.value;
                    if (attrId) {
                      // Get selected options for this attribute from existing attributes
                      const existingAttr = formData.attributes.find(a => a.attribute_id === parseInt(attrId));
                      const selectedOptionIds = existingAttr ? existingAttr.option_ids : [];
                      handleAttributeSelect(parseInt(attrId), selectedOptionIds);
                      e.target.value = ''; // Reset dropdown
                    }
                  }}
                  value=""
                >
                  <option value="">Select an attribute to add...</option>
                  {attributes.map(attr => (
                    <option 
                      key={attr.id} 
                      value={attr.id}
                      disabled={formData.attributes.some(a => a.attribute_id === attr.id)}
                    >
                      {attr.name}
                      {formData.attributes.some(a => a.attribute_id === attr.id) && ' (Already Added)'}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Selected attributes section */}
            {formData.attributes.length > 0 ? (
              <div className="selected-attributes">
                <h4>Selected Attributes</h4>
                {formData.attributes.map((attr, index) => {
                  const attribute = attributes.find(a => a.id === attr.attribute_id);
                  if (!attribute) return null;
                  
                  return (
                    <div key={attr.attribute_id} className="selected-attribute-card">
                      <div className="attribute-header">
                        <h5>{attribute.name}</h5>
                        <button
                          type="button"
                          className="btn-remove-attribute"
                          onClick={() => removeAttribute(attr.attribute_id)}
                          title="Remove this attribute"
                        >
                          <FaTimes />
                        </button>
                      </div>
                      
                      <div className="options-selection">
                        <label>Available Options:</label>
                        <div className="options-grid">
                          {attribute.options?.map(opt => (
                            <label key={opt.id} className="option-checkbox">
                              <input
                                type="checkbox"
                                checked={attr.option_ids.includes(opt.id)}
                                onChange={(e) => {
                                  const newOptionIds = e.target.checked
                                    ? [...attr.option_ids, opt.id]
                                    : attr.option_ids.filter(id => id !== opt.id);
                                  
                                  // Update the attribute in the list
                                  setFormData(prev => ({
                                    ...prev,
                                    attributes: prev.attributes.map((a, idx) =>
                                      idx === index
                                        ? { ...a, option_ids: newOptionIds }
                                        : a
                                    ),
                                  }));
                                }}
                              />
                              <span>
                                {opt.value}
                                {opt.additional_price > 0 && (
                                  <span className="option-price">(+৳{parseFloat(opt.additional_price).toLocaleString()})</span>
                                )}
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="no-attributes-message">
                <p>No attributes selected yet. Use the dropdown above to add attributes to this product.</p>
              </div>
            )}
          </div>

          {/* Images Section - Full Width */}
          <div className="form-section full-width">
            <h3>Product Images</h3>
            <div className="image-upload">
              <input
                type="file"
                id="images"
                name="images"
                accept="image/*"
                multiple
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <label htmlFor="images" className="btn btn-secondary upload-label">
                <FaImage /> Upload Images
              </label>
              <p className="upload-hint">Drag & drop or click to upload. Multiple images allowed.</p>
              
              {previewImages.length > 0 && (
                <div className="image-previews">
                  {previewImages.map((img, index) => (
                    <div key={index} className="image-preview">
                      <img src={img.url} alt={img.name} />
                      <button
                        type="button"
                        className="remove-image"
                        onClick={() => removeImage(index)}
                        aria-label={`Remove ${img.name}`}
                      >
                        <FaTrash />
                      </button>
                      {img.existing && <span className="existing-badge">Existing</span>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="form-actions">
          {isEditing && (
            <button type="button" className="btn btn-danger" onClick={handleDelete}>
              <FaTrash /> Delete Product
            </button>
          )}
          <div className="actions-right">
            <button type="button" className="btn btn-secondary" onClick={() => navigate('/admin/products')}>               
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving...' : isEditing ? 'Update Product' : 'Create Product'}
              <FaSave />
            </button>
          </div>
        </div>
      </form>

      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={confirmDelete}
        title="Delete Product"
        message="Are you sure you want to delete this product? This action cannot be undone."
        confirmText="Delete"
        type="danger"
      />
    </div>
  );
}

export default AdminProductForm;