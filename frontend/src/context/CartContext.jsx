import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { getCart, addToCart, updateCartItem, deleteCartItem, clearCart } from '../api/services';

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
        const data = await getCart(cartSessionId);
        if (mounted) setCart(data);
      } catch {
        if (mounted) setCart({ items: [], total_items: 0, total_price: '0' });
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

  return (
    <CartContext.Provider
      value={{
        cart,
        cartSessionId,
        cartCount,
        cartTotal,
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