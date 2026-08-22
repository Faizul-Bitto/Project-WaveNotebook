import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { getProductDiscounts } from '../api/services';

function ProductCard({ product }) {
  const [discountInfo, setDiscountInfo] = useState(null);

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
      } catch {
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

  const formattedBadge = useMemo(() => {
    if (!badge) return null;
    // Convert BOGO-style badges like "3+1" / "4+1" into readable text
    const bogoMatch = badge.match(/^(\d+)\s*\+\s*(\d+)\s*(free)?$/i);
    if (bogoMatch) {
      return `Buy ${bogoMatch[1]} Get ${bogoMatch[2]} Free`;
    }
    // Leave other badges (e.g. "5% off", "Free Shipping") as-is
    return badge;
  }, [badge]);

  return (
    <div className="product-card">
      <Link to={`/product/${product.slug}`} className="product-card-link">
        <div className="product-image-wrap">
          <img src={imageUrl} alt={product.name} className="product-image" loading="lazy" />
          {badge && (
            <span className={`product-badge badge-${badgeType === 'free_shipping' ? 'success' : 'danger'}`}>
              {formattedBadge}
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
              <span className="shipping-badge">🚚 Free Shipping</span>
            )}
          </div>
        </div>
      </Link>
    </div>
  );
}

export default ProductCard;
