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

export const adminToggleProductFeatured = async (id, isFeatured) => {
  const { data } = await api.patch(`/admin/products/${id}/feature`, {
    is_featured: isFeatured,
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

export const adminSearchOrders = async (type, value, params = {}) => {
  const { data } = await api.get('/admin/orders/search', {
    params: { type, value, ...params },
  });
  return data;
};

export const adminGetOrderStatusCounts = async () => {
  const { data } = await api.get('/admin/orders/status-counts');
  return data;
};

// ------------------------------------------
// Admin - Exports (Excel / CSV downloads)
// ------------------------------------------
// Downloads a file blob from an export endpoint and triggers the browser
// download. Respects the same filters the pages pass as query params.
async function downloadExport (url, params, fallbackName) {
  const { data, headers } = await api.get(url, { params, responseType: 'blob' });
  const cd = headers['content-disposition'] || '';
  const match = cd.match(/filename="?([^";]+)"?/);
  const filename = match ? match[1] : fallbackName;
  const blobUrl = window.URL.createObjectURL(data);
  const link = document.createElement('a');
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(blobUrl);
  return filename;
}

export const adminExportOrders = async (params = {}, suffix = 'xlsx') =>
  downloadExport('/admin/orders/export', { format: suffix, ...params }, `orders.${suffix}`);

export const adminExportUsers = async (params = {}, suffix = 'xlsx') =>
  downloadExport('/admin/users/export', { format: suffix, ...params }, `users.${suffix}`);

export const adminExportProducts = async (params = {}, suffix = 'xlsx') =>
  downloadExport('/admin/products/export', { format: suffix, ...params }, `products.${suffix}`);

export const adminExportExpenses = async (params = {}, suffix = 'xlsx') =>
  downloadExport('/admin/expenses/export', { format: suffix, ...params }, `expenses.${suffix}`);

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

export const adminReorderBanners = async (order) => {
  const { data } = await api.put('/admin/banners/reorder', { order });
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

// ==========================================
// Admin - Expense Types
// ==========================================
export const adminGetExpenseTypes = async (params = {}) => {
  const { data } = await api.get('/admin/expenses/types', { params });
  return data;
};

export const adminCreateExpenseType = async (typeData) => {
  const { data } = await api.post('/admin/expenses/types', typeData);
  return data;
};

export const adminUpdateExpenseType = async (id, typeData) => {
  const { data } = await api.put(`/admin/expenses/types/${id}`, typeData);
  return data;
};

export const adminDeleteExpenseType = async (id) => {
  const { data } = await api.delete(`/admin/expenses/types/${id}`);
  return data;
};

// ==========================================
// Admin - Payment By
// ==========================================
export const adminGetPaymentByList = async (params = {}) => {
  const { data } = await api.get('/admin/expenses/payment-by', { params });
  return data;
};

export const adminCreatePaymentBy = async (payload) => {
  const { data } = await api.post('/admin/expenses/payment-by', payload);
  return data;
};

export const adminUpdatePaymentBy = async (id, payload) => {
  const { data } = await api.put(`/admin/expenses/payment-by/${id}`, payload);
  return data;
};

export const adminDeletePaymentBy = async (id) => {
  const { data } = await api.delete(`/admin/expenses/payment-by/${id}`);
  return data;
};

// ==========================================
// Admin - Payment Methods
// ==========================================
export const adminGetPaymentMethods = async (params = {}) => {
  const { data } = await api.get('/admin/expenses/payment-methods', { params });
  return data;
};

export const adminCreatePaymentMethod = async (payload) => {
  const { data } = await api.post('/admin/expenses/payment-methods', payload);
  return data;
};

export const adminUpdatePaymentMethod = async (id, payload) => {
  const { data } = await api.put(`/admin/expenses/payment-methods/${id}`, payload);
  return data;
};

export const adminDeletePaymentMethod = async (id) => {
  const { data } = await api.delete(`/admin/expenses/payment-methods/${id}`);
  return data;
};

// ==========================================
// Admin - Expenses
// ==========================================
export const adminGetExpenses = async (params = {}) => {
  const { data } = await api.get('/admin/expenses', { params });
  return data;
};

export const adminGetExpense = async (id) => {
  const { data } = await api.get(`/admin/expenses/${id}`);
  return data;
};

export const adminCreateExpense = async (expenseData) => {
  const { data } = await api.post('/admin/expenses', expenseData);
  return data;
};

export const adminUpdateExpense = async (id, expenseData) => {
  const { data } = await api.put(`/admin/expenses/${id}`, expenseData);
  return data;
};

export const adminDeleteExpense = async (id) => {
  const { data } = await api.delete(`/admin/expenses/${id}`);
  return data;
};

export const adminGetExpenseSummary = async (params = {}) => {
  const { data } = await api.get('/admin/expenses/summary', { params });
  return data;
};

export const adminGetExpenseDropdowns = async () => {
  const { data } = await api.get('/admin/expenses/dropdown');
  return data;
};

// ==========================================
// Admin - Discounts
// ==========================================
export const adminGetDiscounts = async (params = {}) => {
  const { data } = await api.get('/admin/discounts', { params });
  return data;
};

export const adminGetDiscount = async (id) => {
  const { data } = await api.get(`/admin/discounts/${id}`);
  return data;
};

export const adminCreateDiscount = async (discountData) => {
  const { data } = await api.post('/admin/discounts', discountData);
  return data;
};

export const adminUpdateDiscount = async (id, discountData) => {
  const { data } = await api.put(`/admin/discounts/${id}`, discountData);
  return data;
};

export const adminDeleteDiscount = async (id) => {
  const { data } = await api.delete(`/admin/discounts/${id}`);
  return data;
};

export const adminToggleDiscountStatus = async (id, status) => {
  const { data } = await api.patch(`/admin/discounts/${id}/status`, { status });
  return data;
};

export const adminGetDiscountUsage = async (id, params = {}) => {
  const { data } = await api.get(`/admin/discounts/${id}/usage`, { params });
  return data;
};

// ==========================================
// Admin - Order Adjustments (manual discount)
// ==========================================
export const adminGetOrderAdjustments = async (orderId) => {
  const { data } = await api.get(`/admin/orders/${orderId}/adjustments`);
  return data;
};

export const adminCreateOrderAdjustment = async (orderId, adjustmentData) => {
  const { data } = await api.post(`/admin/orders/${orderId}/adjustments`, adjustmentData);
  return data;
};

export const adminDeleteOrderAdjustment = async (orderId, adjustmentId) => {
  const { data } = await api.delete(`/admin/orders/${orderId}/adjustments/${adjustmentId}`);
  return data;
};

export const adminCalculateOrderPreview = async (items) => {
  const { data } = await api.post('/admin/orders/calculate', { items });
  return data;
};

// ==========================================
// Admin - Shipping Charges
// ==========================================
export const adminGetShippingCharges = async () => {
  const { data } = await api.get('/admin/shipping-charges');
  return data;
};

export const adminCreateShippingCharge = async (chargeData) => {
  const { data } = await api.post('/admin/shipping-charges', chargeData);
  return data;
};

export const adminUpdateShippingCharge = async (id, chargeData) => {
  const { data } = await api.put(`/admin/shipping-charges/${id}`, chargeData);
  return data;
};

export const adminDeleteShippingCharge = async (id) => {
  const { data } = await api.delete(`/admin/shipping-charges/${id}`);
  return data;
};

// ==========================================
// Contact Messages (Admin)
// ==========================================
export const adminGetContacts = async (params = {}) => {
  const { data } = await api.get('/admin/contacts', { params });
  return data;
};

export const adminGetUnreadMessageCount = async () => {
  const { data } = await api.get('/admin/contacts/unread-count');
  return data;
};

export const adminMarkMessageRead = async (id) => {
  const { data } = await api.patch(`/admin/contacts/${id}/read`);
  return data;
};

export const adminDeleteMessage = async (id) => {
  const { data } = await api.delete(`/admin/contacts/${id}`);
  return data;
};

export const adminCreateInvoiceTicket = async (orderId) => {
  const { data } = await api.post(`/admin/orders/${orderId}/invoice-ticket`);
  return data;
};
