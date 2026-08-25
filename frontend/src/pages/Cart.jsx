import { useState } from 'react';
import { Link } from 'react-router-dom';
import { FaTrash, FaShoppingCart, FaArrowLeft, FaSync, FaGift } from 'react-icons/fa';
import { useCart } from '../context/CartContext';
import { useToast } from '../context/ToastContext';
import Modal from '../components/Modal';

function Cart() {
  const { cart, loading, fetchCart, updateItem, removeItem, clearAll, totalDiscount, totalAfterDiscount, discountBreakdown, freeShipping, winningRule, pendingBogoOffers, simpleBogo, bogoFreeNote } = useCart();
  const { addToast, toastPromise } = useToast();
  const [showClearModal, setShowClearModal] = useState(false);
  const [bogoUpdating, setBogoUpdating] = useState(false);

  // Handle customer accepting a partial (<100%) BOGO offer.
  // We map the pending offer's product_id to the matching cart item and
  // increase its quantity to buy_quantity + get_quantity (= current + extra units).
  const handleAcceptBogo = async (offer) => {
    const match = (cart?.items || []).find((it) => it.product_id === offer.product_id);
    if (!match) return;

    const newQty = match.quantity + (offer.extra_units || offer.get_quantity || 1);
    if (newQty > (match.available_stock || 0)) {
      addToast(`Only ${match.available_stock} item(s) available in stock.`, 'error');
      return;
    }

    setBogoUpdating(true);
    try {
      // Morphing promise toast: "Applying..." -> success / error blob
      await toastPromise(
        (async () => {
          const result = await updateItem(match.id, newQty);
          if (!result.success) {
            const err = new Error(result.error || 'Failed to apply BOGO offer.');
            err.isExpected = true;
            throw err;
          }
          return result;
        })(),
        {
          loading: 'Applying BOGO offer...',
          success: `BOGO applied — ${offer.extra_units} more added at ${offer.get_discount_percent}% off!`,
          error: (err) => (err && err.message) || 'Failed to apply BOGO offer.',
        },
        { showProgress: true }
      );
    } catch {
      // Error already shown by the promise toast
    } finally {
      setBogoUpdating(false);
    }
  };

  const handleQuantityChange = async (itemId, newQuantity, availableStock) => {
    if (newQuantity < 1) return;
    if (newQuantity > availableStock) {
      addToast( `Only ${ availableStock } item(s) available in stock.`, 'error' );
      return;
    }
    await updateItem(itemId, newQuantity);
  };

  const handleRemove = async (itemId) => {
    await removeItem(itemId);
  };

  const handleClear = async () => {
    setShowClearModal(true);
  };

  const handleRefresh = async () => {
    await fetchCart();
    addToast('Stock refreshed.', 'success');
  };

  const confirmClear = async () => {
    setShowClearModal(false);
    const result = await clearAll();
    if (result.success) {
      addToast('Cart cleared!', 'success');
    } else {
      addToast(result.error || 'Failed to clear cart.', 'error');
    }
  };

  // Build a BOGO label for an item that has free/discounted bonus units.
  // For 100% free BOGO: bonus items are added on top (show "+ N FREE").
  // For partial (<100%) BOGO: discounted items are within the purchased
  // quantity — no extra badge shown; the discount appears in the summary.
  const getBogoInfo = (item) => {
    const bonus = item.bonus_quantity || item.bogo_bonus_quantity || 0;
    if (!bonus) return null;
    const pct = item.bogo_get_discount_percent;
    const isFullFree = pct != null && pct >= 100;
    if (!isFullFree) return null; // Partial BOGO: discount shown in summary, not as extra badge
    const label = `${bonus} FREE`;
    return { bonus, label, isFullFree };
  };

  if (loading) {
    return <div className="container loading">Loading cart...</div>;
  }

  const items = cart?.items || [];

  if (items.length === 0) {
    return (
      <div className="container empty-state">
        <FaShoppingCart className="empty-icon" />
        <h2>Your cart is empty</h2>
        <p>Browse our products and add items to your cart.</p>
        <Link to="/products" className="btn btn-primary">Start Shopping</Link>
      </div>
    );
  }

  return (
    <div className="cart-page">
      <div className="container">
        <div className="page-header">
          <h1>Shopping Cart</h1>
          <div className="header-actions">
            <button className="btn btn-outline" onClick={handleRefresh} aria-label="Refresh stock">
              <FaSync /> Refresh Stock
            </button>
            <button className="btn btn-outline" onClick={handleClear}>
              Clear Cart
            </button>
          </div>
        </div>

        <div className="cart-layout">
          {/* Cart Items */}
          <div className="cart-items">
            {/* Pending BOGO opt-in offers (partial <100% BOGO awaiting consent) */}
            {pendingBogoOffers && pendingBogoOffers.length > 0 && (
              <div className="cart-bogo-offers-section">
                {pendingBogoOffers.map((offer, idx) => (
                  <div className="bogo-offer-box" key={idx}>
                    <div className="bogo-offer-icon"><FaGift /></div>
                    <div className="bogo-offer-content">
                      <span className="bogo-offer-title">
                        🎁 Get one more for just ৳{parseFloat(offer.extra_unit_price || 0).toLocaleString()} ({parseInt(offer.get_discount_percent)}% off)!
                      </span>
                      <span className="bogo-offer-desc">
                        BOGO Offer: Buy {offer.buy_quantity} get {offer.get_quantity} at {parseInt(offer.get_discount_percent)}% off
                      </span>
                    </div>
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => handleAcceptBogo(offer)}
                      disabled={bogoUpdating}
                    >
                      {bogoUpdating ? 'Adding...' : `Add for ৳${parseFloat(offer.extra_total || 0).toLocaleString()}`}
                    </button>
                  </div>
                ))}
              </div>
            )}

            {items.map((item) => (
              <div className="cart-item" key={item.id}>
                <Link to={`/product/${item.slug}`} className="cart-item-image">
                  <img
                    src={item.image_url || 'https://placehold.co/100x100?text=No+Image'}
                    alt={item.product_name}
                  />
                </Link>

                <div className="cart-item-info">
                   <Link to={`/product/${item.slug}`} className="cart-item-name">
                     {item.product_name}
                   </Link>
                   {item.selected_attributes_display && (
                     <p className="cart-item-attributes">{item.selected_attributes_display}</p>
                   )}
                   <p className="cart-item-price">৳{parseFloat(item.unit_price).toLocaleString()} / unit</p>
                    {item.available_stock !== undefined && (
                      <span className="cart-item-stock">
                        {item.available_stock > 0
                          ? item.quantity > item.available_stock
                            ? <span className="stock-warning-small">Only {item.available_stock} left - reduce quantity</span>
                            : `${item.available_stock} in stock`
                          : <span className="stock-warning-small out-of-stock">Out of stock</span>}
                      </span>
                    )}
                 </div>

                  <div className="cart-item-qty-wrapper">
                    <div className="cart-item-quantity">
                      <button
                        onClick={() => handleQuantityChange(item.id, item.quantity - 1, item.available_stock)}
                        aria-label="Decrease quantity"
                        disabled={item.quantity <= 1}
                      >
                        -
                      </button>
                      <span>{item.quantity}</span>
                      <button
                        onClick={() => handleQuantityChange(item.id, item.quantity + 1, item.available_stock)}
                        aria-label="Increase quantity"
                        disabled={item.quantity >= (item.available_stock || 0)}
                        title={item.available_stock ? `Only ${item.available_stock} in stock` : 'Out of stock'}
                      >
                        +
                      </button>
                    </div>
                    {getBogoInfo(item) && (
                      <span className="cart-bogo-badge" title="Extra units added free via BOGO">
                        + {getBogoInfo(item).label} (BOGO)
                      </span>
                    )}
                    {item.available_stock !== undefined && item.available_stock !== null && item.quantity >= (item.available_stock || 0) && (
                      <span className="cart-qty-limit">
                        {item.available_stock > 0
                          ? `Only ${item.available_stock} in stock - max quantity reached`
                          : 'Out of stock'}
                      </span>
                    )}
                  </div>

                  <div className="cart-item-subtotal">
                    <span>৳{parseFloat(item.discounted_subtotal || item.subtotal).toLocaleString()}</span>
                    {getBogoInfo(item) && (
                      <span className="cart-bogo-note">includes {getBogoInfo(item).bonus} free</span>
                    )}
                  </div>

                 <button
                   className="cart-item-remove"
                   onClick={() => handleRemove(item.id)}
                   aria-label={`Remove ${item.product_name} from cart`}
                 >
                   <FaTrash />
                 </button>
              </div>
            ))}
          </div>

          {/* Order Summary */}
          <div className="cart-summary">
            <h2>Order Summary</h2>
            <div className="summary-row">
              <span>Items ({cart?.total_items || 0})</span>
              <span>৳{parseFloat(cart?.total_price || '0').toLocaleString()}</span>
            </div>

            {simpleBogo && bogoFreeNote && (
              <div className="summary-row summary-row-bogo-note">
                <span>{bogoFreeNote}</span>
              </div>
            )}

            {!simpleBogo && bogoFreeNote && (
              <div className="summary-row summary-row-bogo-note">
                <span>{bogoFreeNote}</span>
              </div>
            )}

            {discountBreakdown && discountBreakdown.length > 0 && (
              <>
                {discountBreakdown.map((entry, idx) => {
                  const isBogoFree = entry.type === 'bogo' && parseFloat(entry.get_discount_percent || entry['get_discount_percent'] || 0) >= 100;
                  return (
                    <div className="summary-row summary-row-discount" key={idx}>
                      <span>
                        {entry.name || (entry.type === 'price_discount' ? 'Discount' : entry.type)}
                      </span>
                      <span className="discount-amount">
                        {isBogoFree ? 'FREE' : `-৳${parseFloat(entry.amount || 0).toLocaleString()}`}
                      </span>
                    </div>
                  );
                })}
              </>
            )}

            {freeShipping && (
              <div className="summary-row summary-row-free-shipping">
                <span><span className="fs-badge">🚚</span> Free Shipping</span>
                <span className="free-shipping-text">FREE</span>
              </div>
            )}

            {simpleBogo !== true && totalDiscount > 0 && (
              <div className="summary-row summary-row-total-discount">
                <span>Total Discount</span>
                <span className="discount-amount">-৳{totalDiscount.toLocaleString()}</span>
              </div>
            )}

            <div className="summary-row summary-row-shipping">
              <span>Delivery</span>
              <span>Calculated at checkout</span>
            </div>

            <div className="summary-total">
              <span>Total</span>
              <span>৳{totalAfterDiscount.toLocaleString()}</span>
            </div>

            {items.some(i => !i.available_stock || i.available_stock === 0 || i.quantity > (i.available_stock || 0)) && (
              <div className="cart-stock-warning">
                Some items are out of stock or have insufficient quantity. Please review your cart before checkout.
              </div>
            )}

            <Link
              to="/checkout"
              className="btn btn-primary btn-lg checkout-btn"
              onClick={() => {
                const hasStockIssues = items.some(i => !i.available_stock || i.available_stock === 0 || i.quantity > (i.available_stock || 0));
                if (hasStockIssues) {
                  addToast('Some items are out of stock or exceed available quantity. Please fix your cart before checkout.', 'error');
                  return false;
                }
              }}
            >
              Proceed to Checkout
            </Link>
            <Link to="/products" className="continue-shopping">
              <FaArrowLeft /> Continue Shopping
            </Link>
          </div>
        </div>

        <Modal
          isOpen={showClearModal}
          onClose={() => setShowClearModal(false)}
          onConfirm={confirmClear}
          title="Clear Cart"
          message="Are you sure you want to clear your cart?"
          confirmText="Clear All"
          type="danger"
        />
      </div>
    </div>
  );
}

export default Cart;