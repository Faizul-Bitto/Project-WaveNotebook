import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { FaShoppingCart, FaCheckCircle } from 'react-icons/fa';
import { useCart } from '../context/CartContext';
import { useToast } from '../context/ToastContext';
import { getProductDiscounts } from '../api/services';

function ProductCard({ product }) {
  const { addItem } = useCart();
  const { addToast } = useToast();
  const [added, setAdded] = useState(false);
  const [discountInfo, setDiscountInfo] = useState(null);
  const cardRef = useRef(null);

  const validFiles = (product.files || []).filter((f) => f.file_url);
  const imageUrl = validFiles?.[0]?.file_url || 'https://placehold.co/300x300?text=No+Image';

  const priceMin = product.price_range ? parseFloat(product.price_range.min) : 0;
  const priceMax = product.price_range ? parseFloat(product.price_range.max) : 0;

  useEffect(() => {
    const fetchDiscountInfo = async () => {
      try {
        const unitPrice = priceMin || priceMax || 0;
        const data = await getProductDiscounts(product.id, unitPrice);
        if (data?.discount_info) {
          setDiscountInfo(data.discount_info);
        }
      } catch (err) {
        // Silently ignore - product just won't have discount info
      }
    };
    fetchDiscountInfo();
  }, [product.id, priceMin, priceMax]);

  const displayPrice = priceMax > 0
    ? (priceMin === priceMax
      ? `৳${priceMax.toLocaleString()}`
      : `৳${priceMin.toLocaleString()} - ৳${priceMax.toLocaleString()}`)
    : '৳0';

  const inStockVariants = product.in_stock_variants || [];
  const isInStock = inStockVariants.length > 0 || product.is_in_stock;

  const firstInStockAttrs = inStockVariants.length > 0
    ? (() => {
        try {
          return JSON.parse(inStockVariants[0]);
        } catch {
          return null;
        }
      })()
    : null;

  const badge = discountInfo?.badge;
  const badgeType = discountInfo?.badge_type;
  const hasDiscount = badge && badgeType !== 'free_shipping';
  const isFreeShipping = discountInfo?.free_shipping;
  const discountedPrice = discountInfo?.discounted_price;
  const originalPrice = discountInfo?.original_price;
  const discountedRange = discountInfo?.discounted_price_range;
  const originalRange = discountInfo?.original_price_range;
  const hasDiscountRange = !!discountedRange &&
    parseFloat(discountedRange.min) !== parseFloat(discountedRange.max);

  const handleAddToCart = async (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (!isInStock) {
      addToast('This product is out of stock.', 'error');
      return;
    }

    const selectedAttributes = {};
    const attrs = product.attributes || [];

    if (firstInStockAttrs && attrs.length > 0) {
      attrs.forEach((attr) => {
        const options = attr.options || [];
        const attrName = attr.name.toLowerCase();
        const matchingValue = firstInStockAttrs[attr.name] || firstInStockAttrs[attr.slug] || firstInStockAttrs[attrName];
        if (matchingValue) {
          const option = options.find((opt) => opt.value === matchingValue);
          if (option) {
            selectedAttributes[attr.id] = option.id;
          }
        }
      });
    }

    const attrsString = Object.keys(selectedAttributes).length > 0
      ? JSON.stringify(selectedAttributes)
      : null;

    const result = await addItem(product.id, 1, attrsString);
    if (result.success) {
      setAdded(true);
      setTimeout(() => setAdded(false), 2000);
      triggerFlyToCart(cardRef.current);
      addToast('Added to cart!', 'success');
    } else {
      addToast(result.error || 'Failed to add to cart.', 'error');
    }
  };

  return (
    <div className="product-card" ref={cardRef}>
      <Link to={`/product/${product.slug}`} className="product-card-link">
        <div className="product-image-wrap">
          <img src={imageUrl} alt={product.name} className="product-image" loading="lazy" />
          {badge && (
            <span className={`product-badge badge-${badgeType === 'free_shipping' ? 'success' : 'danger'}`}>
              {badge}
            </span>
          )}
          {!isInStock && (
            <span className="product-out-of-stock">Out of Stock</span>
          )}
        </div>
        <div className="product-info">
          <h3 className="product-name">{product.name}</h3>
          <div className="product-price-row">
            {hasDiscount && hasDiscountRange ? (
              <span className="product-price-group">
                <span className="product-price-original">৳{parseFloat(originalRange.min).toLocaleString()} - ৳{parseFloat(originalRange.max).toLocaleString()}</span>
                <span className="product-price-discounted">৳{parseFloat(discountedRange.min).toLocaleString()} - ৳{parseFloat(discountedRange.max).toLocaleString()}</span>
              </span>
            ) : hasDiscount && discountedPrice ? (
              <span className="product-price-group">
                <span className="product-price-original">৳{parseFloat(originalPrice || priceMax).toLocaleString()}</span>
                <span className="product-price-discounted">৳{parseFloat(discountedPrice).toLocaleString()}</span>
              </span>
            ) : (
              <span className="product-price">{displayPrice}</span>
            )}
            {isFreeShipping && !hasDiscount && (
              <span className="shipping-badge">🚚 ফ্রি শিপিং</span>
            )}
          </div>
        </div>
      </Link>
      <button
        className="add-to-cart-btn"
        onClick={handleAddToCart}
        disabled={!isInStock}
      >
        {added ? <><FaCheckCircle /> Added</> : <><FaShoppingCart /> Add to Cart</>}
      </button>
    </div>
  );
}

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

export default ProductCard;
