import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { FaSearch, FaTimes, FaThLarge, FaTh, FaThList } from 'react-icons/fa';
import { getProducts, getCategories } from '../api/services';
import ProductCard from '../components/ProductCard';
import { useToast } from '../context/ToastContext';

const ITEMS_PER_PAGE = 12;

function Products() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [selectedCategory, setSelectedCategory] = useState(searchParams.get('category') || '');
  const [priceMin, setPriceMin] = useState(searchParams.get('price_min') || '');
  const [priceMax, setPriceMax] = useState(searchParams.get('price_max') || '');
  const [sortBy, setSortBy] = useState(searchParams.get('sort') || 'default');
  const [viewMode, setViewMode] = useState('grid-4');
  const [categoriesLoaded, setCategoriesLoaded] = useState(false);
  const { addToast } = useToast();

  const categoryId = searchParams.get('category') || '';
  const searchQuery = searchParams.get('search') || '';

  const flattenCategories = (cats) => {
    const result = [];
    const flatten = (items) => {
      items.forEach((cat) => {
        result.push({ id: cat.id, name: cat.name, product_count: cat.product_count });
        if (cat.children && cat.children.length) flatten(cat.children);
      });
    };
    flatten(cats);
    return result;
  };

  const fetchProducts = useCallback(async (offset = 0, append = false) => {
    try {
      if (!append) setLoading(true);
      else setLoadingMore(true);

      const params = {
        skip: offset,
        limit: ITEMS_PER_PAGE,
      };
      if (categoryId) params.category_id = categoryId;
      if (searchQuery) params.search = searchQuery;
      if (priceMin) params.price_min = parseFloat(priceMin);
      if (priceMax) params.price_max = parseFloat(priceMax);
      if (sortBy && sortBy !== 'default') params.sort_by = sortBy;

      const productData = await getProducts(params);
      const fetched = productData.products || [];
      setProducts(append ? (prev) => [...prev, ...fetched] : fetched);
      setTotal(productData.total || 0);
      setHasMore(offset + ITEMS_PER_PAGE < (productData.total || 0));
    } catch (error) {
      console.error('Failed to load products:', error);
      addToast('Failed to load products.', 'error');
    } finally {
      if (!append) setLoading(false);
      else setLoadingMore(false);
    }
  }, [categoryId, searchQuery, priceMin, priceMax, sortBy, addToast]);

  useEffect(() => {
    const loadCategories = async () => {
      try {
        const data = await getCategories(true);
        const cats = data.categories || [];
        setCategories(cats);
        setCategoriesLoaded(true);
      } catch (err) {
        console.error('Failed to load categories:', err);
        setCategoriesLoaded(true);
      }
    };
    loadCategories();
  }, []);

  const flatCategories = flattenCategories(categories);

  useEffect(() => {
    if (categoriesLoaded && !categoryId && !searchQuery && flatCategories.length > 0) {
      const firstCatId = String(flatCategories[0].id);
      const autoSelect = () => {
        setSelectedCategory(firstCatId);
        const params = new URLSearchParams();
        params.set('category', firstCatId);
        setSearchParams(params);
      };
      autoSelect();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categoriesLoaded, categoryId, flatCategories]);

  useEffect(() => {
    const loadProducts = async () => {
      await fetchProducts(0, false);
    };
    loadProducts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categoryId, searchQuery, priceMin, priceMax, sortBy]);

  const handleLoadMore = useCallback(() => {
    const offset = products.length;
    fetchProducts(offset, true);
  }, [fetchProducts, products.length]);

  const handleCategoryClick = (catId) => {
    setSearch('');
    const params = new URLSearchParams();
    if (catId) params.set('category', catId);
    setSearchParams(params);
    setSelectedCategory(catId);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (search.trim()) {
      params.set('search', search.trim());
    }
    if (priceMin) params.set('price_min', priceMin);
    if (priceMax) params.set('price_max', priceMax);
    if (sortBy && sortBy !== 'default') params.set('sort', sortBy);
    setSearchParams(params);
  };

  const handlePriceFilter = () => {
    const params = new URLSearchParams(searchParams);
    if (priceMin) params.set('price_min', priceMin);
    else params.delete('price_min');
    if (priceMax) params.set('price_max', priceMax);
    else params.delete('price_max');
    setSearchParams(params);
  };

  const clearFilters = () => {
    setSearch('');
    setPriceMin('');
    setPriceMax('');
    setSortBy('default');
    const params = new URLSearchParams();
    if (flatCategories.length > 0 && selectedCategory) {
      params.set('category', selectedCategory);
    } else if (flatCategories.length > 0) {
      params.set('category', String(flatCategories[0].id));
    }
    setSearchParams(params);
  };

  const handleSortChange = (e) => {
    const value = e.target.value;
    setSortBy(value);
    const params = new URLSearchParams(searchParams);
    if (value && value !== 'default') {
      params.set('sort', value);
    } else {
      params.delete('sort');
    }
    setSearchParams(params);
  };

  const gridClass = viewMode === 'grid-4' ? 'products-grid products-grid-4'
    : viewMode === 'grid-2' ? 'products-grid products-grid-2'
    : 'products-grid products-grid-3';

  const showClearFilters = priceMin || priceMax || searchQuery || sortBy !== 'default';

  return (
    <div className="products-page">
      <div className="container">
        <div className="page-header">
          <h1>All Products</h1>
          <p>{total} products found</p>
        </div>

        <div className="products-layout">
          {/* Sidebar */}
          <aside className="products-sidebar">
            {/* Categories */}
            <div className="sidebar-section">
              <h3 className="sidebar-title">Categories</h3>
              <ul className="category-list">
                {flatCategories.map((cat) => (
                   <li
                     key={cat.id}
                     className={`category-item ${searchQuery ? '' : (selectedCategory === String(cat.id) ? 'active' : '')}`}
                     onClick={() => handleCategoryClick(String(cat.id))}
                   >
                    <span className="category-name">{cat.name}</span>
                    {cat.product_count !== undefined && (
                      <span className="category-count">({cat.product_count})</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>

            {/* Price Range */}
            <div className="sidebar-section">
              <h3 className="sidebar-title">Price</h3>
              <div className="price-range">
                <div className="price-inputs">
                  <input
                    type="number"
                    placeholder="Min"
                    value={priceMin}
                    onChange={(e) => setPriceMin(e.target.value)}
                    className="price-input"
                  />
                  <span className="price-separator">—</span>
                  <input
                    type="number"
                    placeholder="Max"
                    value={priceMax}
                    onChange={(e) => setPriceMax(e.target.value)}
                    className="price-input"
                  />
                </div>
                <button className="btn btn-outline btn-sm" onClick={handlePriceFilter}>
                  Go
                </button>
              </div>
            </div>

            {/* Clear Filters - only show for non-category filters */}
            {showClearFilters && (
              <div className="sidebar-section">
                <button className="btn btn-outline btn-sm w-full" onClick={clearFilters}>
                  <FaTimes /> Clear All Filters
                </button>
              </div>
            )}
          </aside>

          {/* Main Content */}
          <main className="products-main">
            {/* Top Bar with Search, Sorting and View Mode */}
            <div className="products-toolbar">
              <form className="filter-search" onSubmit={handleSearchSubmit}>
                <input
                  type="text"
                  placeholder="Search products..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <button type="submit" className="btn btn-primary btn-sm">
                  <FaSearch />
                </button>
              </form>

              <div className="toolbar-right">
                <select
                  className="sort-select"
                  value={sortBy}
                  onChange={handleSortChange}
                >
                  <option value="default">Default sorting</option>
                  <option value="latest">Sort by latest</option>
                  <option value="price_asc">Sort by price: low to high</option>
                  <option value="price_desc">Sort by price: high to low</option>
                </select>

                <div className="view-mode-toggle">
                  <button
                    className={`view-mode-btn ${viewMode === 'grid-4' ? 'active' : ''}`}
                    onClick={() => setViewMode('grid-4')}
                    title="4 per row"
                  >
                    <FaThLarge />
                  </button>
                  <button
                    className={`view-mode-btn ${viewMode === 'grid-3' ? 'active' : ''}`}
                    onClick={() => setViewMode('grid-3')}
                    title="3 per row"
                  >
                    <FaTh />
                  </button>
                  <button
                    className={`view-mode-btn ${viewMode === 'grid-2' ? 'active' : ''}`}
                    onClick={() => setViewMode('grid-2')}
                    title="2 per row"
                  >
                    <FaThList />
                  </button>
                </div>
              </div>
            </div>

            {/* Products Grid */}
            {loading ? (
              <div className="loading">Loading products...</div>
            ) : products.length === 0 ? (
              <div className="empty-state">
                <h3>No products found</h3>
                <p>Try adjusting your search or filter criteria.</p>
              </div>
            ) : (
              <div className={gridClass}>
                {products.map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>
            )}

            {/* Load More */}
            {!loading && hasMore && (
              <div className="load-more-container">
                <button
                  className="btn btn-primary btn-lg"
                  onClick={handleLoadMore}
                  disabled={loadingMore}
                >
                  {loadingMore ? 'Loading...' : 'Load More'}
                </button>
              </div>
            )}

            {!loading && !hasMore && products.length > 0 && (
              <div className="load-more-container">
                <p className="no-more-text">You've seen all products.</p>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}

export default Products;
