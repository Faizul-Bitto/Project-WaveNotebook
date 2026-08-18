import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import {
  FaTachometerAlt,
  FaBox,
  FaShoppingBag,
  FaTags,
  FaUsers,
  FaImage,
  FaSignOutAlt,
  FaBars,
  FaTimes,
  FaCubes,
  FaCog,
  FaReceipt,
  FaChevronDown,
  FaChevronRight,
  FaTruck,
} from 'react-icons/fa';

function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [expensesExpanded, setExpensesExpanded] = useState(
    location.pathname.startsWith('/admin/expenses')
  );

  useEffect(() => {
    if (location.pathname.startsWith('/admin/expenses')) {
      setExpensesExpanded(true);
    }
  }, [location.pathname]);

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    navigate('/admin/login');
  };

  const navItems = [
    { path: '/admin/dashboard', label: 'Dashboard', icon: <FaTachometerAlt /> },
    { path: '/admin/banners', label: 'Banners', icon: <FaImage /> },
    { path: '/admin/settings', label: 'Settings', icon: <FaCog /> },
    { path: '/admin/users', label: 'Users', icon: <FaUsers /> },
    { path: '/admin/categories', label: 'Categories', icon: <FaTags /> },
    { path: '/admin/attributes', label: 'Attributes', icon: <FaCubes /> },
    { path: '/admin/products', label: 'Products', icon: <FaBox /> },
    { path: '/admin/orders', label: 'Orders', icon: <FaShoppingBag /> },
    { path: '/admin/discounts', label: 'Discounts', icon: <FaTags /> },
    { path: '/admin/shipping-charges', label: 'Shipping Charges', icon: <FaTruck /> },
    {
      label: 'Expenses',
      icon: <FaReceipt />,
      subItems: [
        { path: '/admin/expenses', label: 'All Expenses' },
        { path: '/admin/expenses/types', label: 'Expense Types' },
        { path: '/admin/expenses/payment-by', label: 'Payment By' },
        { path: '/admin/expenses/payment-methods', label: 'Payment Methods' },
      ],
    },
  ];

  const isActive = (path) => location.pathname === path;
  const isActiveStartsWith = (path) => location.pathname.startsWith(path);

  return (
    <div className="admin-layout">
      <aside className={`admin-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="admin-sidebar-header">
          <h2>Wave Notebook</h2>
          <p>Admin Panel</p>
          <button
            className="admin-sidebar-close"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close sidebar"
          >
            <FaTimes />
          </button>
        </div>

        <nav className="admin-nav">
          {navItems.map((item) => {
            if (item.subItems) {
              const isActiveThis = isActiveStartsWith(item.subItems[0].path);
              return (
                <div key={item.label}>
                  <button
                    className={`admin-nav-item admin-nav-parent ${isActiveThis ? 'active' : ''}`}
                    onClick={() => setExpensesExpanded(!expensesExpanded)}
                  >
                    <span className="admin-nav-icon">{item.icon}</span>
                    {item.label}
                    <span className="admin-nav-chevron">
                      {expensesExpanded ? <FaChevronDown /> : <FaChevronRight />}
                    </span>
                  </button>
                  {expensesExpanded && (
                    <div className="admin-nav-submenu">
                      {item.subItems.map((sub) => (
                        <Link
                          key={sub.path}
                          to={sub.path}
                          className={`admin-nav-subitem ${isActive(sub.path) ? 'active' : ''}`}
                          onClick={() => setSidebarOpen(false)}
                        >
                          {sub.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              );
            }
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`admin-nav-item ${isActive(item.path) ? 'active' : ''}`}
                onClick={() => setSidebarOpen(false)}
              >
                <span className="admin-nav-icon">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="admin-sidebar-footer">
          <Link to="/" className="admin-nav-item">
            <span className="admin-nav-icon"><FaBars /></span>
            View Website
          </Link>
          <button className="admin-nav-item admin-logout" onClick={handleLogout}>
            <span className="admin-nav-icon"><FaSignOutAlt /></span>
            Logout
          </button>
        </div>
      </aside>

      <div className="admin-main">
        <div className="admin-topbar">
          <button
            className="admin-menu-btn"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open sidebar"
          >
            <FaBars />
          </button>
          <h1>Admin Panel</h1>
        </div>

        <div className="admin-content">
          <Outlet />
        </div>
      </div>

      {sidebarOpen && (
        <div className="admin-overlay" onClick={() => setSidebarOpen(false)} />
      )}
    </div>
  );
}

export default AdminLayout;
