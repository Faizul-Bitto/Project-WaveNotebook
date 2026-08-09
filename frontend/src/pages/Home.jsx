import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FaTruck, FaShieldAlt, FaHeadset, FaMoneyBillWave, FaChevronLeft, FaChevronRight } from 'react-icons/fa';
import { getBanners, getCategories, getProducts } from '../api/services';
import ProductCard from '../components/ProductCard';

function Home() {
  const [banners, setBanners] = useState([]);
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeBanner, setActiveBanner] = useState(0);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [bannerData, categoryData, productData] = await Promise.all([
          getBanners(),
          getCategories(),
          getProducts({ limit: 8 }),
        ]);
        setBanners(bannerData.banners || []);
        setCategories(categoryData.categories || []);
        setProducts(productData.products || []);
      } catch (error) {
        console.error('Failed to load home data:', error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  useEffect(() => {
    if (banners.length <= 1) return;
    const interval = setInterval(() => {
      setActiveBanner((prev) => (prev + 1) % banners.length);
    }, 5000);
    return () => clearInterval(interval);
  }, [banners.length]);

  const features = [
    { icon: <FaTruck />, title: 'Fast Delivery', desc: 'All over Bangladesh' },
    { icon: <FaShieldAlt />, title: 'Quality Products', desc: '100% genuine items' },
    { icon: <FaMoneyBillWave />, title: 'Cash on Delivery', desc: 'Pay when you receive' },
    { icon: <FaHeadset />, title: '24/7 Support', desc: 'We are always here' },
  ];

  return (
    <div className="home-page">
      <section className="hero-banner">
        <div className="container">
          {banners.length > 0 ? (
            <div className="banner-slider">
              {banners.map((banner, index) => (
                <div key={banner.id} className={`banner-slide ${index === activeBanner ? 'active' : ''}`}>
                  <a href={banner.link_url || '#'}>
                    <img src={banner.image_url} alt={banner.title} />
                    <div className="banner-overlay">
                      <h2>{banner.title}</h2>
                      {banner.subtitle && <p>{banner.subtitle}</p>}
                    </div>
                  </a>
                </div>
              ))}
              {banners.length > 1 && (
                <div className="banner-dots">
                  {banners.map((_, index) => (
                    <button key={index} className={`dot ${index === activeBanner ? 'active' : ''}`} onClick={() => setActiveBanner(index)} />
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="hero-placeholder">
              <h1>Wave Notebook</h1>
              <p>Your trusted online shop for quality notebooks & stationery</p>
              <Link to="/products" className="btn btn-primary">Shop Now</Link>
            </div>
          )}
        </div>
      </section>

      <section className="features-section">
        <div className="container features-grid">
          {features.map((feature, index) => (
            <div className="feature-item" key={index}>
              <div className="feature-icon">{feature.icon}</div>
              <div>
                <h4>{feature.title}</h4>
                <p>{feature.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="categories-section">
        <div className="container">
          <div className="section-header">
            <h2>Shop by Category</h2>
            <Link to="/products" className="view-all">View All</Link>
          </div>
          {categories.length > 0 && (
            <CategoryMarquee categories={categories} />
          )}
        </div>
      </section>

      <section className="products-section">
        <div className="container">
          <div className="section-header">
            <h2>Featured Products</h2>
            <Link to="/products" className="view-all">View All</Link>
          </div>
          {loading ? (
            <div className="loading">Loading products...</div>
          ) : (
            <div className="products-grid">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function CategoryMarquee({ categories }) {
  const count = categories.length;
  const PER_VIEW = 3;
  const ITEM_WIDTH = 164; // item width (140px) + right margin (24px)
  const [index, setIndex] = useState(count);
  const [transitioning, setTransitioning] = useState(true);

  // Triple the array so we can loop seamlessly forever
  const items = [...categories, ...categories, ...categories];
  const canScroll = count > PER_VIEW;

  const next = () => {
    if (!canScroll) return;
    setTransitioning(true);
    setIndex((i) => i + 1);
  };

  const prev = () => {
    if (!canScroll) return;
    setTransitioning(true);
    setIndex((i) => i - 1);
  };

  // Auto-flow the carousel continuously
  useEffect(() => {
    if (!canScroll) return;
    const timer = setInterval(() => {
      setTransitioning(true);
      setIndex((i) => i + 1);
    }, 2500);
    return () => clearInterval(timer);
  }, [canScroll]);

  // When we reach a duplicated boundary, jump back seamlessly (no animation)
  const handleTransitionEnd = () => {
    if (index >= count * 2) {
      setTransitioning(false);
      setIndex(index - count);
    } else if (index <= 0) {
      setTransitioning(false);
      setIndex(index + count);
    }
  };

  return (
    <div className="cat-carousel">
      {canScroll && (
        <button className="cat-carousel-arrow cat-carousel-arrow-left" onClick={prev} aria-label="Previous">
          <FaChevronLeft />
        </button>
      )}
      <div className="cat-carousel-window">
        <div
          className="cat-carousel-track"
          style={{
            transform: `translateX(${-(index * ITEM_WIDTH)}px)`,
            transition: transitioning ? 'transform 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)' : 'none',
          }}
          onTransitionEnd={handleTransitionEnd}
        >
          {items.map((category, idx) => (
            <Link to={`/products?category=${category.id}`} className="cat-carousel-item" key={idx}>
              <div className="cat-round">
                {category.image_url ? (
                  <img src={category.image_url} alt={category.name} />
                ) : (
                  <span className="cat-round-icon">📚</span>
                )}
              </div>
              <span className="cat-carousel-name">{category.name}</span>
            </Link>
          ))}
        </div>
      </div>
      {canScroll && (
        <button className="cat-carousel-arrow cat-carousel-arrow-right" onClick={next} aria-label="Next">
          <FaChevronRight />
        </button>
      )}
    </div>
  );
}

export default Home;
