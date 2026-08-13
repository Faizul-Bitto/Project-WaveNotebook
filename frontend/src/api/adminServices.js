import api from './client';

// ==========================================
// Admin - Categories
// ==========================================
export const adminGetCategories = async (params = {}) => {
  const { data } = await api.get('/admin/categories', { params });
  return data;
};

export const adminCreateCategory = async (formData) => {
  const { data } = await api.post('/admin/categories', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const adminUpdateCategory = async (id, formData) => {
  const { data } = await api.put(`/admin/categories/${id}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const adminDeleteCategory = async (id) => {
  const { data } = await api.delete(`/admin/categories/${id}`);
  return data;
};

// ==========================================
// Admin - Attributes
// ==========================================
export const adminGetAttributes = async (params = {}) => {
  const { data } = await api.get('/admin/attributes', { params });
  return data;
};

export const adminCreateAttribute = async (attributeData) => {
  const { data } = await api.post('/admin/attributes', attributeData);
  return data;
};

export const adminUpdateAttribute = async (id, attributeData) => {
  const { data } = await api.put(`/admin/attributes/${id}`, attributeData);
  return data;
};

export const adminDeleteAttribute = async (id) => {
  const { data } = await api.delete(`/admin/attributes/${id}`);
  return data;
};

// ==========================================
// Admin - Attribute Options
// ==========================================
export const adminGetAttributeOptions = async (params = {}) => {
  const { data } = await api.get('/admin/attribute-options', { params });
  return data;
};

export const adminCreateAttributeOption = async (optionData) => {
  const { data } = await api.post('/admin/attribute-options', optionData);
  return data;
};

export const adminUpdateAttributeOption = async (id, optionData) => {
  const { data } = await api.put(`/admin/attribute-options/${id}`, optionData);
  return data;
};

export const adminDeleteAttributeOption = async (id) => {
  const { data } = await api.delete(`/admin/attribute-options/${id}`);
  return data;
};

// ==========================================
// Admin - Products
// ==========================================
export const adminGetProducts = async (params = {}) => {
  const { data } = await api.get('/admin/products', { params });
  return data;
};

export const adminGetProduct = async (id) => {
  const { data } = await api.get(`/admin/products/${id}`);
  return data;
};

export const adminCreateProduct = async (formData) => {
  const { data } = await api.post('/admin/products', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const adminUpdateProduct = async (id, formData) => {
  const { data } = await api.put(`/admin/products/${id}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const adminDeleteProduct = async (id) => {
  const { data } = await api.delete(`/admin/products/${id}`);
  return data;
};

// ==========================================
// Admin - Product Variants
// ==========================================
export const adminGetProductVariants = async (productId) => {
  const { data } = await api.get(`/admin/products/${productId}/variants`);
  return data;
};

export const adminUpdateVariant = async (variantId, variantData) => {
  const { data } = await api.put(`/admin/products/variants/${variantId}`, variantData);
  return data;
};

export const adminBulkUpdateVariants = async (productId, updates) => {
  const { data } = await api.put(`/admin/products/${productId}/variants/bulk`, updates);
  return data;
};

export const adminAddNewVariants = async (productId, newAttributeOptionIds) => {
  const { data } = await api.post(`/admin/products/${productId}/variants`, newAttributeOptionIds);
  return data;
};

export const adminGenerateVariants = async (productId, attributeOptionIds) => {
  const { data } = await api.post(`/admin/products/${productId}/variants/generate`, attributeOptionIds);
  return data;
};

export const adminGenerateVariantsFromProduct = async (productId) => {
  const { data } = await api.post(`/admin/products/${productId}/variants/generate`, null);
  return data;
};

export const adminDeleteVariant = async (variantId) => {
  const { data } = await api.delete(`/admin/products/variants/${variantId}`);
  return data;
};

// ==========================================
// Admin - Orders
// ==========================================
export const adminGetOrders = async (params = {}) => {
  const { data } = await api.get('/admin/orders', { params });
  return data;
};

export const adminCreateOrder = async (orderData) => {
  const { data } = await api.post('/admin/orders', orderData);
  return data;
};

export const adminUpdateOrder = async (id, orderData) => {
  const { data } = await api.put(`/admin/orders/${id}`, orderData);
  return data;
};

export const adminGetOrder = async (id) => {
  const { data } = await api.get(`/admin/orders/${id}`);
  return data;
};

export const adminUpdateOrderStatus = async (id, status) => {
  const { data } = await api.put(`/admin/orders/${id}/status`, { status });
  return data;
};

export const adminDeleteOrder = async (id) => {
  const { data } = await api.delete(`/admin/orders/${id}`);
  return data;
};

export const adminSearchOrders = async (type, value) => {
  const { data } = await api.get('/admin/orders/search', {
    params: { type, value },
  });
  return data;
};

// ==========================================
// Admin - Users
// ==========================================
export const adminGetUsers = async (params = {}) => {
  const { data } = await api.get('/admin/users', { params });
  return data;
};

export const adminGetUser = async (id) => {
  const { data } = await api.get(`/admin/users/${id}`);
  return data;
};

export const adminUpdateUser = async (id, userData) => {
  const { data } = await api.put(`/admin/users/${id}`, userData);
  return data;
};

export const adminDeleteUser = async (id) => {
  const { data } = await api.delete(`/admin/users/${id}`);
  return data;
};

// ==========================================
// Admin - Banners
// ==========================================
export const adminGetBanners = async () => {
  const { data } = await api.get('/admin/banners');
  return data;
};

export const adminCreateBanner = async (formData) => {
  const { data } = await api.post('/admin/banners', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const adminUpdateBanner = async (id, formData) => {
  const { data } = await api.put(`/admin/banners/${id}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const adminDeleteBanner = async (id) => {
  const { data } = await api.delete(`/admin/banners/${id}`);
  return data;
};

export const adminGetSettings = async () => {
  const { data } = await api.get('/admin/settings');
  return data;
};

export const adminUpdateSettings = async (formData) => {
  const { data } = await api.put('/admin/settings', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};
