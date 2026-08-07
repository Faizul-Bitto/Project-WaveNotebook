import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { FaShoppingCart, FaCheckCircle, FaTruck, FaShieldAlt, FaUndo } from 'react-icons/fa';
import { getProductBySlug } from '../api/services';
import { useCart } from '../context/CartContext';

function ProductDetail() {
  const { slug } = useParams();
  const { addItem } = useCart();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [selectedOptions, setSelectedOptions] = useState({});
  const [activeImage, setActiveImage] = useState(0);
  const [added, setAdded] = useState(false);

  useEffect(() => {
    const loadProduct = async () => {
      try {
        setLoading(true);
        const data = await getProductBySlug(slug);
        setProduct(data.product);

        // Auto-select the first option of each attribute by default
        const defaultOptions = {};
        data.product?.attributes?.forEach((attr) => {
          if (attr.options && attr.options.length > 0) {
            defaultOptions[attr.id] = attr.options[0].id;
          }
        });
        setSelectedOptions(defaultOptions);

        setError(null);
      } catch (err) {
        setError(err.response?.data?.detail || 'Product not found');
      } finally {
        setLoading(false);
      }
    };
    loadProduct();
  }, [slug]);

  const handleOptionSelect = (attributeId, optionId) => {
    setSelectedOptions((prev) => ({
      ...prev,
      [attributeId]: optionId,
    }));
  };

  const calculatePrice = () => {
    if (!product) return 0;
    let price = parseFloat(product.base_price || '0');

    // Add additional prices for selected options
    product.attributes?.forEach((attr) => {
      const selectedOptionId = selectedOptions[attr.id];
      if (selectedOptionId) {
        const option = attr.options.find((opt) => opt.id === selectedOptionId);
        if (option) {
          price += parseFloat(option.additional_price || '0');
        }
      }
    });

    return price * quantity;
  };

  const handleAddToCart = async () => {
    // Build selected attributes JSON string with attribute IDs as keys and option IDs as values
    // Format: {"1": 5, "2": 8} where 1,2 are attribute IDs and 5,8 are option IDs
    const selectedAttrs = {};
    product.attributes?.forEach((attr) => {
      const selectedOptionId = selectedOptions[attr.id];
      if (selectedOptionId) {
        selectedAttrs[attr.id] = selectedOptionId;
      }
    });

    const attrsString = Object.keys(selectedAttrs).length > 0
      ? JSON.stringify(selectedAttrs)
      : null;

    const result = await addItem(product.id, quantity, attrsString);
    if (result.success) {
      setAdded(true);
      setTimeout(() => setAdded(false), 2000);
    }
  };

  if (loading) {
    return <div className="container loading">Loading product...</div>;
  }

  if (error || !product) {
    return (
      <div className="container empty-state">
        <h3>{error || 'Product not found'}</h3>
        <Link to="/products" className="btn btn-primary">Back to Products</Link>
      </div>
    );
  }

  const validFiles = (product.files || []).filter((f) => f.file_url);
  const images = validFiles.length > 0 ? validFiles : [{ file_url: 'https://placehold.co/500x500?text=No+Image' }];
  const totalPrice = calculatePrice();

  return (
    <div className="product-detail-page">
      <div className="container">
        {/* Breadcrumb */}
        <nav className="breadcrumb">
          <Link to="/">Home</Link> / <Link to="/products">Products</Link> / <span>{product.name}</span>
        </nav>

        <div className="product-detail-grid">
          {/* Images */}
          <div className="product-images">
            <div className="main-image">
              <img src={images[activeImage]?.file_url} alt={product.name} />
            </div>
            {images.length > 1 && (
              <div className="thumbnail-list">
                {images.map((img, index) => (
                  <button
                    key={img.id || index}
                    className={`thumbnail ${index === activeImage ? 'active' : ''}`}
                    onClick={() => setActiveImage(index)}
                    aria-label={`View image ${index + 1}`}
                  >
                    <img src={img.file_url} alt={`${product.name} ${index + 1}`} />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Product Info */}
          <div className="product-info-detail">
            <h1 className="product-title">{product.name}</h1>
            <p className="product-code">Product Code: {product.product_code}</p>

            <div className="product-price-detail">
              <span className="price">৳{totalPrice.toLocaleString()}</span>
              {quantity > 1 && (
                <span className="unit-price">(৳{(totalPrice / quantity).toLocaleString()} / unit)</span>
              )}
            </div>

            {product.is_in_stock ? (
              <span className="stock-badge in-stock">✓ In Stock</span>
            ) : (
              <span className="stock-badge out-of-stock">✗ Out of Stock</span>
            )}

            {/* Attributes */}
            {product.attributes?.length > 0 && (
              <div className="attributes-section">
                {product.attributes.map((attr) => (
                  <div className="attribute-group" key={attr.id}>
                    <h4 className="attribute-name">{attr.name}:</h4>
                    <div className="attribute-options">
                      {attr.options.map((option) => (
                        <button
                          key={option.id}
                          className={`attribute-option-btn ${
                            selectedOptions[attr.id] === option.id ? 'selected' : ''
                          }`}
                          onClick={() => handleOptionSelect(attr.id, option.id)}
                        >
                          {option.value}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Quantity */}
            <div className="quantity-section">
              <h4>Quantity:</h4>
              <div className="quantity-control">
                <button
                  onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                  aria-label="Decrease quantity"
                >
                  -
                </button>
                <span>{quantity}</span>
                <button
                  onClick={() => setQuantity((q) => q + 1)}
                  aria-label="Increase quantity"
                >
                  +
                </button>
              </div>
            </div>

            {/* Add to Cart */}
            <button
              className="btn btn-primary btn-lg add-to-cart-detail"
              onClick={handleAddToCart}
              disabled={!product.is_in_stock}
            >
              {added ? <><FaCheckCircle /> Added to Cart</> : <><FaShoppingCart /> Add to Cart</>}
            </button>

            {/* Trust badges */}
            <div className="trust-badges">
              <div className="trust-item">
                <FaTruck />
                <span>Fast Delivery</span>
              </div>
              <div className="trust-item">
                <FaShieldAlt />
                <span>Quality Guarantee</span>
              </div>
              <div className="trust-item">
                <FaUndo />
                <span>Easy Returns</span>
              </div>
            </div>
          </div>
        </div>

        {/* Description */}
        <div className="product-description">
          <h2>Product Description</h2>
          <p>{product.description || 'No description available.'}</p>
          {product.specifications && (
            <>
              <h3>Specifications</h3>
              <p>{product.specifications}</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default ProductDetail;