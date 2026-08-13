import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { FaShoppingCart, FaBolt, FaCheckCircle, FaTruck, FaShieldAlt, FaUndo } from 'react-icons/fa';
import { getProductBySlug, findVariant, getDefaultVariant } from '../api/services';
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
  const [currentVariant, setCurrentVariant] = useState(null);
  const [variantLoading, setVariantLoading] = useState(false);
  const [variantError, setVariantError] = useState(null);
  const pageRef = useRef(null);

  useEffect(() => {
    const loadProduct = async () => {
      try {
        setLoading(true);
        const data = await getProductBySlug(slug);
        setProduct(data.product);
        setSelectedOptions({});
        setCurrentVariant(null);
        setVariantError(null);

        // Auto-load default variant (preferably in-stock)
        try {
          const variantData = await getDefaultVariant(data.product.id);
          if (variantData.variant) {
            setCurrentVariant(variantData.variant);

            // Auto-select the attribute options matching the default variant
            const defaultAttrs = variantData.variant.selected_attributes || {};
            const newSelectedOptions = {};
            (data.product.attributes || []).forEach((attr) => {
              const optionValue = defaultAttrs[attr.name];
              if (optionValue) {
                const option = attr.options.find((opt) => opt.value === optionValue);
                if (option) {
                  newSelectedOptions[attr.id] = option.id;
                }
              }
            });
            if (Object.keys(newSelectedOptions).length > 0) {
              setSelectedOptions(newSelectedOptions);
            }
          }
        } catch {
          // No variant available, keep null
        }
      } catch (err) {
        addToast(err.response?.data?.detail || 'Product not found', 'error');
      } finally {
        setLoading(false);
      }
    };
    loadProduct();
  }, [slug]);

  // Find variant when all attributes are selected
  useEffect(() => {
    if (!product) return;

    const attributes = product.attributes || [];

    // If no attributes, just get the single variant
    if (attributes.length === 0) {
      let cancelled = false;
      const loadSingleVariant = async () => {
        setVariantLoading(true);
        try {
          const data = await findVariant(product.id, {});
          if (!cancelled) {
            setCurrentVariant(data.variant);
          }
        } catch (err) {
          if (!cancelled) {
            setCurrentVariant(null);
            setVariantError(err.response?.data?.detail || 'Variant not available.');
          }
        } finally {
          if (!cancelled) {
            setVariantLoading(false);
          }
        }
      };
      loadSingleVariant();
      return () => { cancelled = true; };
    }

    const allSelected = attributes.every((attr) => selectedOptions[attr.id]);

    if (!allSelected) {
      return;
    }

    let cancelled = false;

    const findVariantForSelection = async () => {
      setVariantLoading(true);
      setVariantError(null);
      try {
        // Build selected attributes with names as keys
        const selectedAttrs = {};
        attributes.forEach((attr) => {
          const optionId = selectedOptions[attr.id];
          const option = attr.options.find((opt) => opt.id === optionId);
          if (option) {
            selectedAttrs[attr.name] = option.value;
          }
        });

        const data = await findVariant(product.id, selectedAttrs);
        if (!cancelled) {
          setCurrentVariant(data.variant);
        }
      } catch (err) {
        if (!cancelled) {
          setCurrentVariant(null);
          setVariantError(err.response?.data?.detail || 'Variant not available.');
        }
      } finally {
        if (!cancelled) {
          setVariantLoading(false);
        }
      }
    };

    findVariantForSelection();

    return () => {
      cancelled = true;
    };
  }, [product, selectedOptions]);

  const handleOptionSelect = (attributeId, optionId) => {
    setSelectedOptions((prev) => ({
      ...prev,
      [attributeId]: optionId,
    }));
  };

  // Check if every attribute has a selected option
  const missingAttributes = (product?.attributes || []).filter(
    (attr) => !selectedOptions[attr.id]
  );

  const allSelected = missingAttributes.length === 0;
  const variantInStock = currentVariant?.in_stock && currentVariant?.stock_quantity > 0;

  const handleBuyNow = async () => {
    if (!allSelected) {
      addToast('Please select all options before buying.', 'error');
      return;
    }

    if (!currentVariant || !variantInStock) {
      addToast('This variant is out of stock.', 'error');
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
    setDirectItem({ product, selectedOptions, quantity, attrsString, variant: currentVariant });
    navigate('/checkout');
  };

  const handleAddToCart = async () => {
    if (!allSelected) {
      addToast('Please select all options before adding to cart.', 'error');
      return;
    }

    if (!currentVariant || !variantInStock) {
      addToast('This variant is out of stock.', 'error');
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

  // Display price: exact variant price if selected, otherwise price range
  const displayPrice = currentVariant?.price
    ? parseFloat(currentVariant.price)
    : null;
  const priceRange = product.price_range;

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
              {displayPrice ? (
                <>
                  <span className="price">৳{displayPrice.toLocaleString()}</span>
                  {quantity > 1 && (
                    <span className="unit-price">(৳{(displayPrice * quantity).toLocaleString()} total)</span>
                  )}
                </>
              ) : priceRange ? (
                <span className="price-range">
                  {parseFloat(priceRange.min) === parseFloat(priceRange.max)
                    ? `৳${parseFloat(priceRange.min).toLocaleString()}`
                    : `Starting from ৳${parseFloat(priceRange.min).toLocaleString()} - ৳${parseFloat(priceRange.max).toLocaleString()}`}
                </span>
              ) : (
                <span className="price">৳0</span>
              )}
            </div>

            {allSelected && currentVariant ? (
              variantInStock ? (
                <span className="stock-badge in-stock">✓ In Stock</span>
              ) : (
                <span className="stock-badge out-of-stock">✗ Out of Stock</span>
              )
            ) : variantError ? (
              <span className="stock-badge out-of-stock">✗ {variantError}</span>
            ) : (
              <span className="stock-badge in-stock">✓ In Stock</span>
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
              disabled={!allSelected || !currentVariant || !variantInStock || variantLoading}
            >
              {added ? <><FaCheckCircle /> Added to Cart</> : <><FaShoppingCart /> Add to Cart</>}
            </button>

            {/* Buy Now */}
            <button
              className="btn btn-success btn-lg add-to-cart-detail"
              onClick={handleBuyNow}
              disabled={!allSelected || !currentVariant || !variantInStock || variantLoading}
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