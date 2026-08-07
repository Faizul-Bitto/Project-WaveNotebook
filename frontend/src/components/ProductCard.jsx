import { Link } from 'react-router-dom';
import { FaShoppingCart, FaCheckCircle } from 'react-icons/fa';
import { useCart } from '../context/CartContext';
import { useState } from 'react';

function ProductCard({ product }) {
  const { addItem } = useCart();
  const [added, setAdded] = useState(false);

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
    }
  };

  return (
    <div className="product-card">
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

export default ProductCard;