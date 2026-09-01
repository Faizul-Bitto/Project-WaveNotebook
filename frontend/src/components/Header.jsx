import { useEffect, useRef, useState } from 'react';
import { FaEnvelope, FaPhoneAlt, FaSearch, FaShippingFast, FaShoppingCart, FaTimes, FaUserShield } from 'react-icons/fa';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { searchProducts } from '../api/services';
import { useCart } from '../context/CartContext';
import { useSiteSettings } from '../context/SiteSettingsContext';
import { withVersion } from '../utils/media';

function Header () {
  const { settings } = useSiteSettings();
  const { cartCount } = useCart();
  const logoUrl = withVersion( settings.logo_url, settings.updated_at );
  const siteName = settings.site_name || 'WaveNotebook';
  const navigate = useNavigate();
  const location = useLocation();
  const isProductsPage = location.pathname === '/products';
  const [ searchOpen, setSearchOpen ] = useState( false );
  const [ searchQuery, setSearchQuery ] = useState( '' );
  const [ searchResults, setSearchResults ] = useState( [] );
  const [ searchLoading, setSearchLoading ] = useState( false );
  const searchInputRef = useRef( null );
  const headerRef = useRef( null );

  // Expose the real header height as a CSS variable so pages can
  // size full-screen sections (e.g. home hero) against it.
  useEffect( () => {
    const el = headerRef.current;
    if ( !el ) return undefined;
    const setVar = () => {
      document.documentElement.style.setProperty( '--header-height', `${ el.offsetHeight }px` );
    };
    setVar();
    const observer = new ResizeObserver( setVar );
    observer.observe( el );
    return () => observer.disconnect();
  }, [] );

  const closeSearch = () => {
    setSearchOpen( false );
    setSearchQuery( '' );
    setSearchResults( [] );
  };

  const [ scrolled, setScrolled ] = useState( false );

  useEffect( () => {
    const handleScroll = () => {
      setScrolled( window.scrollY > 50 );
    };
    window.addEventListener( 'scroll', handleScroll );
    return () => window.removeEventListener( 'scroll', handleScroll );
  }, [] );

  useEffect( () => {
    if ( !searchQuery ) {
      setSearchResults( [] );
      return;
    }
    const timer = setTimeout( async () => {
      try {
        setSearchLoading( true );
        const data = await searchProducts( searchQuery, 8 );
        setSearchResults( data.products || [] );
      } catch {
        setSearchResults( [] );
      } finally {
        setSearchLoading( false );
      }
    }, 300 );
    return () => clearTimeout( timer );
  }, [ searchQuery ] );

  useEffect( () => {
    const handleEscape = ( e ) => {
      if ( e.key === 'Escape' ) {
        closeSearch();
      }
    };
    document.addEventListener( 'keydown', handleEscape );
    if ( searchOpen ) {
      // Lock scroll WITHOUT layout shift: compensate for the removed scrollbar
      const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
      document.body.style.overflow = 'hidden';
      if ( scrollbarWidth > 0 ) {
        document.body.style.paddingRight = `${ scrollbarWidth }px`;
      }
    } else {
      document.body.style.overflow = '';
      document.body.style.paddingRight = '';
    }
    return () => {
      document.removeEventListener( 'keydown', handleEscape );
      document.body.style.overflow = '';
      document.body.style.paddingRight = '';
    };
  }, [ searchOpen ] );

  return (
    <header ref={ headerRef } className={ `header ${ scrolled ? 'scrolled' : '' }` }>
      {/* Top bar */ }
      <div className="top-bar">
        <div className="container top-bar-inner">
          <div className="top-bar-center">
            <FaPhoneAlt className="top-bar-icon" />
            <a
              href={ `tel:${ ( settings.hotline_number || '01700-000000' ).replace( /[^+\d]/g, '' ) }` }
              className="top-bar-link"
            >
              Hotline: { settings.hotline_number || '01700-000000' }
            </a>
            <span className="top-bar-divider">|</span>
            <FaEnvelope className="top-bar-icon" />
            <a
              href={ `mailto:${ settings.contact_email || 'info@wavenotebook.com' }` }
              className="top-bar-link"
            >
              Email: { settings.contact_email || 'info@wavenotebook.com' }
            </a>
            <span className="top-bar-divider">|</span>
            <Link to="/admin/login" className="top-bar-link">
              <FaUserShield className="top-bar-icon" /> Admin
            </Link>
          </div>
        </div>
      </div>

      {/* Main header */ }
      <div className="main-header">
        <div className="main-header-inner">
          <Link to="/" className="logo">
            { logoUrl ? (
              <img src={ logoUrl } alt={ siteName } className="logo-img" />
            ) : (
              <span className="logo-icon">📓</span>
            ) }
            <span className="logo-text">{ siteName }</span>
          </Link>

          {/* Center navigation */ }
          <nav className="header-nav">
            <Link to="/" className={ `header-nav-link ${ location.pathname === '/' ? 'active' : '' }` }>
              Home
            </Link>
            <Link to="/products" className={ `header-nav-link ${ isProductsPage ? 'active' : '' }` }>
              Shop
            </Link>
            <Link to="/contact" className={ `header-nav-link ${ location.pathname === '/contact' ? 'active' : '' }` }>
              Contact
            </Link>
          </nav>

          <div className="header-actions">
            { isProductsPage ? null : (
              <div className="search-dropdown">
                <button
                  type="button"
                  className={ `search-btn ${ searchOpen ? 'active' : '' }` }
                  onClick={ () => { setSearchOpen( !searchOpen ); if ( !searchOpen ) setTimeout( () => searchInputRef.current?.focus(), 100 ); } }
                  title="Search products"
                >
                  <FaSearch />
                </button>

                {/* Always rendered so open/close transitions animate smoothly */ }
                <div className={ `search-overlay ${ searchOpen ? 'search-overlay-open' : '' }` }>
                  <div className="search-overlay-nav">
                    <div className="container search-overlay-container">
                      <div className="search-overlay-input-wrapper">
                        <FaSearch className="search-overlay-input-icon" />
                        <input
                          ref={ searchInputRef }
                          type="text"
                          className="search-input-overlay"
                          placeholder="Search products..."
                          value={ searchQuery }
                          onChange={ ( e ) => setSearchQuery( e.target.value ) }
                          onKeyDown={ ( e ) => {
                            if ( e.key === 'Enter' && searchQuery.trim() ) {
                              navigate( `/products?search=${ encodeURIComponent( searchQuery.trim() ) }` );
                              closeSearch();
                            }
                          } }
                        />
                      </div>
                      <button
                        type="button"
                        className="search-close-btn"
                        onClick={ closeSearch }
                        title="Cancel search"
                      >
                        <FaTimes />
                      </button>
                    </div>
                  </div>

                  <div className="search-overlay-body">
                    { searchLoading ? (
                      <div className="search-overlay-loading">Searching...</div>
                    ) : searchResults.length === 0 && searchQuery ? (
                      <div className="search-overlay-no-results">No products found</div>
                    ) : searchQuery ? (
                      <div className="search-results-grid">
                        { searchResults.map( ( product ) => {
                          const priceMin = product.price_range ? parseFloat( product.price_range.min ) : 0;
                          const priceMax = product.price_range ? parseFloat( product.price_range.max ) : 0;
                          const displayPrice = priceMax > 0
                            ? ( priceMin === priceMax
                              ? `৳${ priceMax.toLocaleString() }`
                              : `৳${ priceMin.toLocaleString() } - ৳${ priceMax.toLocaleString() }` )
                            : '৳0';
                          const imageUrl = ( product.files || [] ).find( ( f ) => f.file_url )?.file_url || 'https://placehold.co/100x100?text=No+Image';
                          return (
                            <div
                              key={ product.id }
                              className="search-result-card"
                              onClick={ () => {
                                navigate( `/products/${ product.slug || product.id }` );
                                closeSearch();
                              } }
                            >
                              <img src={ imageUrl } alt={ product.name } className="search-result-image" />
                              <div className="search-result-info">
                                <span className="search-result-name">{ product.name }</span>
                                <span className="search-result-price">{ displayPrice }</span>
                              </div>
                            </div>
                          );
                        } ) }
                      </div>
                    ) : (
                      <div className="search-placeholder">Start typing to search products...</div>
                    ) }
                  </div>
                </div>
              </div>
            ) }
            <Link to="/track-order" className="track-order-btn" title="Track your order">
              <FaShippingFast />
              <span className="track-order-label">Order Track</span>
            </Link>
            <Link to="/cart" className="cart-icon-only cart-btn">
              <FaShoppingCart />
              { cartCount > 0 && (
                <span className="cart-count">{ cartCount }</span>
              ) }
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;