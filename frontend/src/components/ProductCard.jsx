import { Link } from 'react-router-dom';
import { FaShoppingCart, FaCheckCircle } from 'react-icons/fa';
import { useCart } from '../context/CartContext';
import { useState, useRef } from 'react';

function ProductCard({ product }) {
  const { addItem } = useCart();
  const [added, setAdded] = useState(false);
  const cardRef = useRef(null);

  const validFiles = (product.files || []).filter((f) => f.file_url);
  const imageUrl = validFiles?.[0]?.file_url || 'https://placehold.co/300x300?text=No+Image';
  const price = parseFloat(product.base_price || '0');

  const handleAddToCart = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    const result = await addItem(product.id, 1, null);
    if (result.success) {
      setAdded(true);
      setTimeout(() => setAdded(false), 2000);
      // Trigger fly-to-cart animation
      triggerFlyToCart(cardRef.current);
    }
  };

  return (
    <div className="product-card" ref={cardRef}>
      <Link to={`/product/${product.slug}`} className="product-card-link">
        <div className="product-image-wrap">
          <img src={imageUrl} alt={product.name} className="product-image" loading="lazy" />
          {!product.is_in_stock && (
            <span className="product-out-of-stock">Out of Stock</span>
          )}
        </div>
        <div className="product-info">
          <h3 className="product-name">{product.name}</h3>
          <div className="product-price-row">
            <span className="product-price">৳{price.toLocaleString()}</span>
          </div>
        </div>
      </Link>
      <button
        className="add-to-cart-btn"
        onClick={handleAddToCart}
        disabled={!product.is_in_stock}
      >
        {added ? <><FaCheckCircle /> Added</> : <><FaShoppingCart /> Add to Cart</>}
      </button>
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

  // Create flying element
  const flyEl = document.createElement('div');
  flyEl.className = 'fly-to-cart';
  flyEl.textContent = '📦';
  document.body.appendChild(flyEl);

  // Set start position (center of the card)
  const startX = sourceRect.left + sourceRect.width / 2;
  const startY = sourceRect.top + sourceRect.height / 2;

  // Set end position (center of cart icon)
  const endX = cartRect.left + cartRect.width / 2;
  const endY = cartRect.top + cartRect.height / 2;

  // Position the flying element at start
  flyEl.style.left = `${startX}px`;
  flyEl.style.top = `${startY}px`;

  // Force reflow
  void flyEl.offsetWidth;

  // Animate to cart
  flyEl.style.transform = `translate(${endX - startX}px, ${endY - startY}px) scale(0.3)`;
  flyEl.style.opacity = '0';

  // Remove after animation
  setTimeout(() => {
    flyEl.remove();
    // Add a little bounce to the cart icon
    cartBtn.classList.add('cart-bounce');
    setTimeout(() => cartBtn.classList.remove('cart-bounce'), 500);
  }, 700);
}

export default ProductCard;
