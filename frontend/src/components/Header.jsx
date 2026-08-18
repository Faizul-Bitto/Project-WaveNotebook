import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useRef } from 'react';
import { FaShoppingCart, FaSearch, FaPhoneAlt, FaUserShield } from 'react-icons/fa';
import { useSiteSettings } from '../context/SiteSettingsContext';
import { useCart } from '../context/CartContext';

function Header() {
  const { settings } = useSiteSettings();
  const { cartCount } = useCart();
  const logoUrl = settings.logo_url;
  const siteName = settings.site_name || 'WaveNotebook';
  const navigate = useNavigate();
  const headerRef = useRef(null);

  const handleSearch = (e) => {
    e.preventDefault();
    const query = e.target.elements.search.value.trim();
    if (query) {
      navigate(`/products?search=${encodeURIComponent(query)}`);
    }
  };

  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      if (headerRef.current) {
        setScrolled(headerRef.current.scrollY > 50);
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header className={`header ${scrolled ? 'scrolled' : ''}`} ref={headerRef}>
      {/* Top bar */}
      <div className="top-bar">
        <div className="container top-bar-inner">
          <div className="top-bar-left">
            <FaPhoneAlt className="top-bar-icon" />
            <span>Hotline: {settings.hotline_number || '01700-000000'}</span>
          </div>
          <div className="top-bar-right">
            <Link to="/track-order" className="top-bar-link">
              Track Order
            </Link>
            <Link to="/admin/login" className="top-bar-link">
              <FaUserShield className="top-bar-icon" /> Admin
            </Link>
          </div>
        </div>
      </div>

      {/* Main header */}
      <div className="main-header">
        <div className="container main-header-inner">
          <Link to="/" className="logo">
            {logoUrl ? (
              <img src={logoUrl} alt={siteName} className="logo-img" />
            ) : (
              <span className="logo-icon">📓</span>
            )}
            <span className="logo-text">{siteName}</span>
          </Link>

          <form className="search-bar" onSubmit={handleSearch}>
            <input
              type="text"
              name="search"
              placeholder="Search products..."
              className="search-input"
            />
            <button type="submit" className="search-btn">
              <FaSearch />
            </button>
          </form>

          <Link to="/cart" className="cart-icon-only cart-btn">
            <FaShoppingCart />
            {cartCount > 0 && (
              <span className="cart-count">{cartCount}</span>
            )}
          </Link>
        </div>
      </div>
    </header>
  );
}

export default Header;