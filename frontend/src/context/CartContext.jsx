import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { getCart, addToCart, updateCartItem, deleteCartItem, clearCart, getShippingCharges } from '../api/services';

const CartContext = createContext();

export function CartProvider({ children }) {
  const [cartSessionId] = useState(() => {
    let id = localStorage.getItem('cart_session_id');
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem('cart_session_id', id);
    }
    return id;
  });
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(false);
  const [shippingCharges, setShippingCharges] = useState([]);

  const fetchCart = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getCart(cartSessionId);
      setCart(data);
    } catch (error) {
      console.error('Failed to fetch cart:', error);
      setCart({ items: [], total_items: 0, total_price: '0' });
    } finally {
      setLoading(false);
    }
  }, [cartSessionId]);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const [cartData, shippingData] = await Promise.all([
          getCart(cartSessionId),
          getShippingCharges(),
        ]);
        if (mounted) {
          setCart(cartData);
          setShippingCharges(shippingData.shipping_charges || []);
        }
      } catch {
        if (mounted) {
          setCart({ items: [], total_items: 0, total_price: '0' });
          setShippingCharges([]);
        }
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, [cartSessionId]);

  const addItem = async (productId, quantity = 1, selectedAttributes = null) => {
    try {
      const data = await addToCart(cartSessionId, {
        product_id: productId,
        quantity,
        selected_attributes: selectedAttributes,
      });
      await fetchCart();
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Failed to add to cart' };
    }
  };

  const updateItem = async (itemId, quantity) => {
    try {
      await updateCartItem(cartSessionId, itemId, { quantity });
      await fetchCart();
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Failed to update cart' };
    }
  };

  const removeItem = async (itemId) => {
    try {
      await deleteCartItem(cartSessionId, itemId);
      await fetchCart();
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Failed to remove item' };
    }
  };

  const clearAll = async () => {
    try {
      await clearCart(cartSessionId);
      setCart({ items: [], total_items: 0, total_price: '0' });
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Failed to clear cart' };
    }
  };

  const cartCount = cart?.total_items || 0;
  const cartTotal = parseFloat(cart?.total_price || '0');
  const totalDiscount = cart?.total_discount ? parseFloat(cart.total_discount) : 0;
  const totalAfterDiscount = cart?.total_after_discount ? parseFloat(cart.total_after_discount) : cartTotal;
  const discountBreakdown = cart?.discount_breakdown || [];
  const freeShipping = cart?.free_shipping || false;
  const winningRule = cart?.winning_rule || null;
  // Partial (<100%) BOGO offers awaiting customer consent (opt-in).
  const pendingBogoOffers = cart?.pending_bogo_offers || [];
  const simpleBogo = cart?.simple_bogo || false;
  const bogoFreeNote = cart?.bogo_free_note || null;

  const getShippingChargeForDistrict = useCallback((districtName = '') => {
    if (!shippingCharges.length) return null;
    const normalized = (districtName || '').trim().toLowerCase();
    const matched = shippingCharges.find((charge) => {
      const zone = (charge.zone_name || '').trim().toLowerCase();
      return normalized.includes(zone) || zone.includes(normalized);
    });
    return matched || null;
  }, [shippingCharges]);

  return (
    <CartContext.Provider
      value={{
        cart,
        cartSessionId,
        cartCount,
        cartTotal,
        totalDiscount,
        totalAfterDiscount,
        discountBreakdown,
        freeShipping,
        winningRule,
        pendingBogoOffers,
        simpleBogo,
        bogoFreeNote,
        shippingCharges,
        getShippingChargeForDistrict,
        loading,
        fetchCart,
        addItem,
        updateItem,
        removeItem,
        clearAll,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
}