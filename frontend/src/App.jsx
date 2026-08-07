import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { CartProvider } from './context/CartContext';
import { DirectBuyProvider } from './context/DirectBuyContext';
import Header from './components/Header';
import Footer from './components/Footer';
import Home from './pages/Home';
import Products from './pages/Products';
import ProductDetail from './pages/ProductDetail';
import Cart from './pages/Cart';
import Checkout from './pages/Checkout';
import TrackOrder from './pages/TrackOrder';
import AdminLogin from './pages/admin/AdminLogin';
import AdminLayout from './pages/admin/AdminLayout';
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminProducts from './pages/admin/AdminProducts';
import AdminProductForm from './pages/admin/AdminProductForm';
import AdminOrders from './pages/admin/AdminOrders';
import AdminOrderDetail from './pages/admin/AdminOrderDetail';
import AdminOrderCreate from './pages/admin/AdminOrderCreate';
import AdminCategories from './pages/admin/AdminCategories';
import AdminUsers from './pages/admin/AdminUsers';
import AdminBanners from './pages/admin/AdminBanners';
import AdminAttributes from './pages/admin/AdminAttributes';
import AdminAttributeOptions from './pages/admin/AdminAttributeOptions';

// Protected route component
function ProtectedRoute({ children }) {
  const token = localStorage.getItem('admin_token');
  if (!token) {
    return <Navigate to="/admin/login" replace />;
  }
  return children;
}

function StoreLayout({ children }) {
  return (
    <>
      <Header />
      <main className="main-content">{children}</main>
      <Footer />
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <DirectBuyProvider>
      <CartProvider>
        <Routes>
          {/* Store routes */}
          <Route
            path="/"
            element={
              <StoreLayout>
                <Home />
              </StoreLayout>
            }
          />
          <Route
            path="/products"
            element={
              <StoreLayout>
                <Products />
              </StoreLayout>
            }
          />
          <Route
            path="/product/:slug"
            element={
              <StoreLayout>
                <ProductDetail />
              </StoreLayout>
            }
          />
          <Route
            path="/cart"
            element={
              <StoreLayout>
                <Cart />
              </StoreLayout>
            }
          />
          <Route
            path="/checkout"
            element={
              <StoreLayout>
                <Checkout />
              </StoreLayout>
            }
          />
          <Route
            path="/track-order"
            element={
              <StoreLayout>
                <TrackOrder />
              </StoreLayout>
            }
          />

          {/* Admin routes */}
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route
            path="/admin"
            element={
              <ProtectedRoute>
                <AdminLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="dashboard" element={<AdminDashboard />} />
            <Route path="products" element={<AdminProducts />} />
            <Route path="products/new" element={<AdminProductForm />} />
            <Route path="products/:id/edit" element={<AdminProductForm />} />
            <Route path="orders" element={<AdminOrders />} />
            <Route path="orders/new" element={<AdminOrderCreate />} />
            <Route path="orders/:id" element={<AdminOrderDetail />} />
            <Route path="orders/:id/edit" element={<AdminOrderCreate />} />
            <Route path="categories" element={<AdminCategories />} />
            <Route path="users" element={<AdminUsers />} />
            <Route path="banners" element={<AdminBanners />} />
            <Route path="attributes" element={<AdminAttributes />} />
            <Route path="attribute-options" element={<AdminAttributeOptions />} />
          </Route>

          {/* 404 */}
          <Route
            path="*"
            element={
              <StoreLayout>
                <div className="container empty-state">
                  <h2>Page Not Found</h2>
                  <p>The page you are looking for does not exist.</p>
                  <a href="/" className="btn btn-primary">Go Home</a>
                </div>
              </StoreLayout>
            }
          />
        </Routes>
      </CartProvider>
      </DirectBuyProvider>
    </BrowserRouter>
  );
}

export default App;