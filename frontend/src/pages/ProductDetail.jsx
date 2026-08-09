import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { FaShoppingCart, FaBolt, FaCheckCircle, FaTruck, FaShieldAlt, FaUndo } from 'react-icons/fa';
import { getProductBySlug } from '../api/services';
import { useCart } from '../context/CartContext';
import { useDirectBuy } from '../context/DirectBuyContext';
import { useToast } from '../context/ToastContext';

function ProductDetail() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { addItem } = useCart();
  const { setDirectItem } = useDirectBuy();
  const { addToast } = useToast();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [selectedOptions, setSelectedOptions] = useState({});
  const [activeImage, setActiveImage] = useState(0);
  const [added, setAdded] = useState(false);
  const pageRef = useRef(null);

  useEffect(() => {
    const loadProduct = async () => {
      try {
        setLoading(true);
        const data = await getProductBySlug(slug);
        setProduct(data.product);
        // No auto-selection: leave all options unselected so the user must pick manually
        setSelectedOptions({});
      } catch (err) {
        addToast(err.response?.data?.detail || 'Product not found', 'error');
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

  // Check if every attribute has a selected option
  const missingAttributes = (product?.attributes || []).filter(
    (attr) => !selectedOptions[attr.id]
  );

  const handleBuyNow = async () => {
    // Validate all options are selected
    if (missingAttributes.length > 0) {
      addToast('Please select all options before buying.', 'error');
      return;
    }

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
    setDirectItem({ product, selectedOptions, quantity, attrsString });
    navigate('/checkout');
  };

  const handleAddToCart = async () => {
    // Validate all options are selected
    if (missingAttributes.length > 0) {
      addToast('Please select all options before adding to cart.', 'error');
      return;
    }

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
      triggerFlyToCart(pageRef.current);
      addToast('Added to cart!', 'success');
    } else {
      addToast(result.error || 'Failed to add to cart.', 'error');
    }
  };

  if (loading) {
    return <div className="container loading">Loading product...</div>;
  }

  if (!product) {
    return (
      <div className="container empty-state">
        <h3>Product not found</h3>
        <Link to="/products" className="btn btn-primary">Back to Products</Link>
      </div>
    );
  }

  const validFiles = (product.files || []).filter((f) => f.file_url);
  const images = validFiles.length > 0 ? validFiles : [{ file_url: 'https://placehold.co/500x500?text=No+Image' }];
  const totalPrice = calculatePrice();

  return (
    <div className="product-detail-page" ref={pageRef}>
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

            {/* Attributes - no auto-selection, user must choose */}
            {product.attributes?.length > 0 && (
              <div className="attributes-section">
                {product.attributes.map((attr) => {
                  const isSelected = !!selectedOptions[attr.id];
                  return (
                    <div className="attribute-group" key={attr.id}>
                      <h4 className="attribute-name">
                        {attr.name}:
                        {!isSelected && <span className="attribute-required"> *</span>}
                      </h4>
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
                      {!isSelected && (
                        <p className="attribute-missing-hint">Please select {attr.name.toLowerCase()} to continue.</p>
                      )}
                    </div>
                  );
                })}
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
              disabled={!product.is_in_stock || missingAttributes.length > 0}
            >
              {added ? <><FaCheckCircle /> Added to Cart</> : <><FaShoppingCart /> Add to Cart</>}
            </button>

            {/* Buy Now */}
            <button
              className="btn btn-success btn-lg add-to-cart-detail"
              onClick={handleBuyNow}
              disabled={!product.is_in_stock || missingAttributes.length > 0}
            >
              <FaBolt /> Buy Now
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

// Fly-to-cart animation: creates a flying item that animates from the card to the cart icon
function triggerFlyToCart(sourceEl) {
  if (!sourceEl) return;
  const cartBtn = document.querySelector('.cart-btn');
  if (!cartBtn) return;

  const sourceRect = sourceEl.getBoundingClientRect();
  const cartRect = cartBtn.getBoundingClientRect();

  const startX = sourceRect.left + sourceRect.width / 2;
  const startY = sourceRect.top + sourceRect.height / 2;
  const endX = cartRect.left + cartRect.width / 2;
  const endY = cartRect.top + cartRect.height / 2;

  const deltaX = endX - startX;
  const deltaY = endY - startY;

  const flyEl = document.createElement('div');
  flyEl.className = 'fly-to-cart';
  flyEl.textContent = '🛒';
  document.body.appendChild(flyEl);

  flyEl.style.left = `${startX}px`;
  flyEl.style.top = `${startY}px`;
  flyEl.style.setProperty('--fly-to-x', `${deltaX}px`);
  flyEl.style.setProperty('--fly-to-y', `${deltaY}px`);
  flyEl.style.animation = 'fly-to-cart-parabolic 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards';

  for (let i = 0; i < 6; i++) {
    const sparkle = document.createElement('div');
    sparkle.className = 'cart-sparkle';
    sparkle.style.left = `${startX}px`;
    sparkle.style.top = `${startY}px`;
    sparkle.style.animationDelay = `${i * 0.05}s`;
    sparkle.style.setProperty('--sparkle-rotation', `${i * 60}deg`);
    document.body.appendChild(sparkle);
  }

  setTimeout(() => {
    flyEl.remove();
    document.querySelectorAll('.cart-sparkle').forEach((el) => el.remove());
    cartBtn.classList.add('cart-bounce');
    setTimeout(() => cartBtn.classList.remove('cart-bounce'), 500);
  }, 800);
}

export default ProductDetail;