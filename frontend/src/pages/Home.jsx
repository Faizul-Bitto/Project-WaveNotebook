import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FaTruck, FaShieldAlt, FaHeadset, FaMoneyBillWave } from 'react-icons/fa';
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

  // Auto-rotate banners
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
      {/* Hero Banner */}
      <section className="hero-banner">
        <div className="container">
          {banners.length > 0 ? (
            <div className="banner-slider">
              {banners.map((banner, index) => (
                <div
                  key={banner.id}
                  className={`banner-slide ${index === activeBanner ? 'active' : ''}`}
                >
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
                    <button
                      key={index}
                      className={`dot ${index === activeBanner ? 'active' : ''}`}
                      onClick={() => setActiveBanner(index)}
                      aria-label={`Go to slide ${index + 1}`}
                    />
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

      {/* Features */}
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

      {/* Categories */}
      <section className="categories-section">
        <div className="container">
          <div className="section-header">
            <h2>Shop by Category</h2>
            <Link to="/products" className="view-all">View All</Link>
          </div>
          <div className="categories-grid">
            {categories.map((category) => (
              <Link
                to={`/products?category=${category.id}`}
                className="category-card"
                key={category.id}
              >
                {category.image_url ? (
                  <div className="category-image-wrap">
                    <img src={category.image_url} alt={category.name} className="category-image" />
                  </div>
                ) : (
                  <div className="category-icon">📚</div>
                )}
                <h3>{category.name}</h3>
                {category.children?.length > 0 && (
                  <p>{category.children.length} subcategories</p>
                )}
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Products */}
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

export default Home;