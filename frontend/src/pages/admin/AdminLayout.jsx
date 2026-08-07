import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useState } from 'react';
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
  FaList,
  FaCubes,
} from 'react-icons/fa';

function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    navigate('/admin/login');
  };

  const navItems = [
    { path: '/admin/dashboard', label: 'Dashboard', icon: <FaTachometerAlt /> },
    { path: '/admin/products', label: 'Products', icon: <FaBox /> },
    { path: '/admin/attributes', label: 'Attributes', icon: <FaCubes /> },
    { path: '/admin/orders', label: 'Orders', icon: <FaShoppingBag /> },
    { path: '/admin/categories', label: 'Categories', icon: <FaTags /> },
    { path: '/admin/users', label: 'Users', icon: <FaUsers /> },
    { path: '/admin/banners', label: 'Banners', icon: <FaImage /> },
  ];

  const isActive = (path) => location.pathname.startsWith(path);

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
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`admin-nav-item ${isActive(item.path) ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <span className="admin-nav-icon">{item.icon}</span>
              {item.label}
            </Link>
          ))}
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