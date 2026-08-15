import api from './client';

// ==========================================
// Products
// ==========================================
export const getProducts = async (params = {}) => {
  const { data } = await api.get('/products', { params });
  return data;
};

export const getProductById = async (id) => {
  const { data } = await api.get(`/products/${id}`);
  return data;
};

export const getProductBySlug = async (slug) => {
  const { data } = await api.get(`/products/slug/${slug}`);
  return data;
};

export const findVariant = async (productId, selectedAttributes) => {
  const { data } = await api.post('/products/find-variant', {
    product_id: productId,
    selected_attributes: selectedAttributes,
  });
  return data;
};

export const getDefaultVariant = async (productId) => {
  const { data } = await api.get(`/products/${productId}/default-variant`);
  return data;
};

// ==========================================
// Categories
// ==========================================
export const getCategories = async (includeCounts = false) => {
  const params = includeCounts ? { include_counts: true } : {};
  const { data } = await api.get('/categories', { params });
  return data;
};

export const getCategoryById = async (id) => {
  const { data } = await api.get(`/categories/${id}`);
  return data;
};

// ==========================================
// Banners
// ==========================================
export const getBanners = async () => {
  const { data } = await api.get('/banners');
  return data;
};

export const getSiteSettings = async () => {
  const { data } = await api.get('/settings');
  return data;
};

// ==========================================
// Lookup
// ==========================================
export const getDistricts = async () => {
  const { data } = await api.get('/lookup/districts');
  return data;
};

// ==========================================
// Cart
// ==========================================
export const addToCart = async (cartSessionId, item) => {
  const { data } = await api.post('/cart', item, {
    params: { cart_session_id: cartSessionId },
  });
  return data;
};

export const getCart = async (cartSessionId) => {
  const { data } = await api.get('/cart', {
    params: { cart_session_id: cartSessionId },
  });
  return data;
};

export const updateCartItem = async (cartSessionId, itemId, itemData) => {
  const { data } = await api.put(`/cart/${itemId}`, itemData, {
    params: { cart_session_id: cartSessionId },
  });
  return data;
};

export const deleteCartItem = async (cartSessionId, itemId) => {
  const { data } = await api.delete(`/cart/${itemId}`, {
    params: { cart_session_id: cartSessionId },
  });
  return data;
};

export const clearCart = async (cartSessionId) => {
  const { data } = await api.delete('/cart', {
    params: { cart_session_id: cartSessionId },
  });
  return data;
};

// ==========================================
// Orders
// ==========================================
export const createOrder = async (orderData) => {
  const { data } = await api.post('/orders', orderData);
  return data;
};

export const trackOrder = async (phoneNumber) => {
  const { data } = await api.get(`/orders/track/${phoneNumber}`);
  return data;
};

export const trackOrderByNumber = async (orderNumber) => {
  const { data } = await api.get(`/orders/track-number/${orderNumber}`);
  return data;
};

// ==========================================
// Auth
// ==========================================
export const adminLogin = async (phone_number, password) => {
  const formData = new FormData();
  formData.append('username', phone_number);
  formData.append('password', password);

  const { data } = await api.post('/auth/login', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};