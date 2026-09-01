import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { useEffect } from 'react';
import { CartProvider } from './context/CartContext';
import { DirectBuyProvider } from './context/DirectBuyContext';
import { SiteSettingsProvider } from './context/SiteSettingsContext';
import { ToastProvider } from './context/ToastContext';
import Header from './components/Header';
import Footer from './components/Footer';
import ChatIcons from './components/ChatIcons';
import BackToTop from './components/BackToTop';
import SiteMeta from './components/SiteMeta';
import PageLoader from './components/PageLoader';
import PageTransition from './components/PageTransition';
import Home from './pages/Home';
import Products from './pages/Products';
import ProductDetail from './pages/ProductDetail';
import Cart from './pages/Cart';
import Checkout from './pages/Checkout';
import TrackOrder from './pages/TrackOrder';
import PolicyPage from './pages/PolicyPage';
import AdminLogin from './pages/admin/AdminLogin';
import AdminLayout from './pages/admin/AdminLayout';
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminProducts from './pages/admin/AdminProducts';
import AdminProductForm from './pages/admin/AdminProductForm';
import AdminProductVariants from './pages/admin/AdminProductVariants';
import AdminOrders from './pages/admin/AdminOrders';
import AdminOrderDetail from './pages/admin/AdminOrderDetail';
import AdminOrderCreate from './pages/admin/AdminOrderCreate';
import AdminCategories from './pages/admin/AdminCategories';
import AdminUsers from './pages/admin/AdminUsers';
import AdminBanners from './pages/admin/AdminBanners';
import AdminSettings from './pages/admin/AdminSettings';
import AdminAttributes from './pages/admin/AdminAttributes';
import AdminAttributeOptions from './pages/admin/AdminAttributeOptions';
import AdminExpenses from './pages/admin/ExpenseDashboard';
import AdminExpenseTypes from './pages/admin/ExpenseTypeManagement';
import AdminPaymentBy from './pages/admin/PaymentByManagement';
import AdminPaymentMethods from './pages/admin/PaymentMethodManagement';
import AdminDiscounts from './pages/admin/AdminDiscounts';
import AdminDiscountForm from './pages/admin/AdminDiscountForm';
import AdminShippingCharges from './pages/admin/AdminShippingCharges';
import Offers from './pages/Offers';
import Contact from './pages/Contact';
import AdminMessages from './pages/admin/AdminMessages';

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
      <ChatIcons />
      <BackToTop />
    </>
  );
}

function ContactLayout({ children }) {
  return (
    <>
      <Header />
      <main className="main-content">{children}</main>
      <ChatIcons />
      <BackToTop />
    </>
  );
}

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    const timer = setTimeout(() => {
      window.scrollTo(0, 0);
    }, 200);
    return () => clearTimeout(timer);
  }, [pathname]);
  return null;
}

function AppContent() {
  const location = useLocation();

  return (
    <>
      <PageLoader />
      <ScrollToTop />
      <SiteMeta />
      <AnimatePresence mode="wait" initial={false}>
        <Routes location={location} key={location.pathname}>
          {/* Store routes */}
              <Route
                path="/"
                element={
                  <StoreLayout>
                    <PageTransition><Home /></PageTransition>
                  </StoreLayout>
                }
              />
              <Route
                path="/products"
                element={
                  <StoreLayout>
                    <PageTransition><Products /></PageTransition>
                  </StoreLayout>
                }
              />
              <Route
                path="/product/:slug"
                element={
                  <StoreLayout>
                    <PageTransition><ProductDetail /></PageTransition>
                  </StoreLayout>
                }
              />
              <Route
                path="/cart"
                element={
                  <StoreLayout>
                    <PageTransition><Cart /></PageTransition>
                  </StoreLayout>
                }
              />
              <Route
                path="/checkout"
                element={
                  <StoreLayout>
                    <PageTransition><Checkout /></PageTransition>
                  </StoreLayout>
                }
              />
              <Route
                path="/track-order"
                element={
                  <StoreLayout>
                    <PageTransition><TrackOrder /></PageTransition>
                  </StoreLayout>
                }
              />
              <Route
                path="/offers"
                element={
                  <StoreLayout>
                    <PageTransition><Offers /></PageTransition>
                  </StoreLayout>
                }
              />
              <Route
                path="/contact"
                element={
                  <ContactLayout>
                    <PageTransition><Contact /></PageTransition>
                  </ContactLayout>
                }
              />
              <Route
                path="/privacy-policy"
                element={
                  <StoreLayout>
                    <PageTransition><PolicyPage /></PageTransition>
                  </StoreLayout>
                }
              />
              <Route
                path="/terms-conditions"
                element={
                  <StoreLayout>
                    <PageTransition><PolicyPage /></PageTransition>
                  </StoreLayout>
                }
              />
              <Route
                path="/refund-policy"
                element={
                  <StoreLayout>
                    <PageTransition><PolicyPage /></PageTransition>
                  </StoreLayout>
                }
              />

              {/* Admin routes */}
              <Route path="/admin/login" element={<PageTransition><AdminLogin /></PageTransition>} />
              <Route
                path="/admin"
                element={
                  <ProtectedRoute>
                    <AdminLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Navigate to="/admin/dashboard" replace />} />
                <Route path="dashboard" element={<PageTransition><AdminDashboard /></PageTransition>} />
                <Route path="products" element={<PageTransition><AdminProducts /></PageTransition>} />
                <Route path="products/new" element={<PageTransition><AdminProductForm /></PageTransition>} />
                <Route path="products/:id/edit" element={<PageTransition><AdminProductForm /></PageTransition>} />
                <Route path="products/:id/variants" element={<PageTransition><AdminProductVariants /></PageTransition>} />
                <Route path="orders" element={<PageTransition><AdminOrders /></PageTransition>} />
                <Route path="orders/new" element={<PageTransition><AdminOrderCreate /></PageTransition>} />
                <Route path="orders/:id" element={<PageTransition><AdminOrderDetail /></PageTransition>} />
                <Route path="orders/:id/edit" element={<PageTransition><AdminOrderCreate /></PageTransition>} />
                <Route path="messages" element={<PageTransition><AdminMessages /></PageTransition>} />
                <Route path="categories" element={<PageTransition><AdminCategories /></PageTransition>} />
                <Route path="users" element={<PageTransition><AdminUsers /></PageTransition>} />
                <Route path="banners" element={<PageTransition><AdminBanners /></PageTransition>} />
                <Route path="settings" element={<PageTransition><AdminSettings /></PageTransition>} />
                <Route path="attributes" element={<PageTransition><AdminAttributes /></PageTransition>} />
                <Route path="attribute-options" element={<PageTransition><AdminAttributeOptions /></PageTransition>} />
                <Route path="expenses" element={<PageTransition><AdminExpenses /></PageTransition>} />
                <Route path="expenses/types" element={<PageTransition><AdminExpenseTypes /></PageTransition>} />
                <Route path="expenses/payment-by" element={<PageTransition><AdminPaymentBy /></PageTransition>} />
                <Route path="expenses/payment-methods" element={<PageTransition><AdminPaymentMethods /></PageTransition>} />
                <Route path="discounts" element={<PageTransition><AdminDiscounts /></PageTransition>} />
                <Route path="discounts/new" element={<PageTransition><AdminDiscountForm /></PageTransition>} />
                <Route path="discounts/:id" element={<PageTransition><AdminDiscountForm /></PageTransition>} />
                <Route path="discounts/:id/edit" element={<PageTransition><AdminDiscountForm /></PageTransition>} />
                <Route path="shipping-charges" element={<PageTransition><AdminShippingCharges /></PageTransition>} />
              </Route>

              {/* 404 */}
              <Route
                path="*"
                element={
                  <StoreLayout>
                    <PageTransition>
                      <div className="container empty-state">
                        <h2>Page Not Found</h2>
                        <p>The page you are looking for does not exist.</p>
                        <a href="/" className="btn btn-primary">Go Home</a>
                      </div>
                    </PageTransition>
                  </StoreLayout>
                }
              />
            </Routes>
          </AnimatePresence>
        </>
      );
  }

function App() {
  return (
    <BrowserRouter>
      <SiteSettingsProvider>
      <DirectBuyProvider>
      <CartProvider>
        <ToastProvider>
          <AppContent />
        </ToastProvider>
      </CartProvider>
      </DirectBuyProvider>
      </SiteSettingsProvider>
    </BrowserRouter>
  );
}

export default App;
