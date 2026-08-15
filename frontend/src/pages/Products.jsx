import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { FaSearch } from 'react-icons/fa';
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

  const categoryId = searchParams.get('category') || '';
  const searchQuery = searchParams.get('search') || '';
  const { addToast } = useToast();

  // Load first page whenever filters change or on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const params = {
          skip: 0,
          limit: ITEMS_PER_PAGE,
        };
        if (categoryId) params.category_id = categoryId;
        if (searchQuery) params.search = searchQuery;

        const [productData, categoryData] = await Promise.all([
          getProducts(params),
          getCategories(),
        ]);
        setProducts(productData.products || []);
        setTotal(productData.total || 0);
        setHasMore(ITEMS_PER_PAGE < (productData.total || 0));
        setCategories(categoryData.categories || []);
      } catch (error) {
        console.error('Failed to load products:', error);
        addToast('Failed to load products.', 'error');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [categoryId, searchQuery, addToast]);

  // Append the next page of products
  const handleLoadMore = useCallback(async () => {
    const offset = products.length;
    try {
      setLoadingMore(true);
      const params = {
        skip: offset,
        limit: ITEMS_PER_PAGE,
      };
      if (categoryId) params.category_id = categoryId;
      if (searchQuery) params.search = searchQuery;

      const [productData, categoryData] = await Promise.all([
        getProducts(params),
        getCategories(),
      ]);
      const fetched = productData.products || [];
      setProducts((prev) => [...prev, ...fetched]);
      setTotal(productData.total || 0);
      setHasMore(offset + ITEMS_PER_PAGE < (productData.total || 0));
      setCategories(categoryData.categories || []);
    } catch (error) {
      console.error('Failed to load more products:', error);
      addToast('Failed to load more products.', 'error');
    } finally {
      setLoadingMore(false);
    }
  }, [categoryId, searchQuery, products, addToast]);

  const handleCategoryChange = (e) => {
    const value = e.target.value;
    setSelectedCategory(value);
    const params = new URLSearchParams(searchParams);
    if (value) {
      params.set('category', value);
    } else {
      params.delete('category');
    }
    setSearchParams(params);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const params = new URLSearchParams(searchParams);
    if (search.trim()) {
      params.set('search', search.trim());
    } else {
      params.delete('search');
    }
    setSearchParams(params);
  };

  // Group products by category. Categories is a tree; flatten to a map of id -> name.
  const flattenCategories = (cats) => {
    const map = {};
    const flatten = (items) => {
      items.forEach((cat) => {
        map[cat.id] = cat.name;
        if (cat.children && cat.children.length) flatten(cat.children);
      });
    };
    flatten(cats);
    return map;
  };

  const categoryNameMap = flattenCategories(categories);

  // Group products by their category_id while preserving the order they appear in
  const groupedProducts = [];
  if (!categoryId) {
    const seen = new Set();
    products.forEach((product) => {
      if (!seen.has(product.category_id)) {
        seen.add(product.category_id);
        groupedProducts.push({
          category_id: product.category_id,
          category_name: categoryNameMap[product.category_id] || 'Other',
          products: [],
        });
      }
      const group = groupedProducts.find((g) => g.category_id === product.category_id);
      group.products.push(product);
    });
  }

  // True so we don't render groupedProducts when a specific category is selected
  const isCategoryView = !!categoryId;

  return (
    <div className="products-page">
      <div className="container">
        <div className="page-header">
          <h1>All Products</h1>
          <p>{total} products found</p>
        </div>

        {/* Filters */}
        <div className="filters-bar">
          <form className="filter-search" onSubmit={handleSearchSubmit}>
            <input
              type="text"
              placeholder="Search products..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <button type="submit" className="btn btn-primary">
              <FaSearch /> Search
            </button>
          </form>

          <select
            className="filter-select"
            value={selectedCategory}
            onChange={handleCategoryChange}
          >
            <option value="">All Categories</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>

        {/* Products - Grouped by Category when showing all */}
        {loading ? (
          <div className="loading">Loading products...</div>
        ) : products.length === 0 ? (
          <div className="empty-state">
            <h3>No products found</h3>
            <p>Try adjusting your search or filter criteria.</p>
          </div>
        ) : isCategoryView ? (
          // Specific category selected: show flat grid
          <div className="products-grid">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        ) : (
          // All products: grouped by category
          <div className="category-products">
            {groupedProducts.map((group) => (
              <section key={group.category_id} className="category-section">
                <div className="category-section-header">
                  <h2>{group.category_name}</h2>
                  <span className="category-count">{group.products.length} item{group.products.length !== 1 ? 's' : ''}</span>
                </div>
                <div className="products-grid">
                  {group.products.map((product) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>
              </section>
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
      </div>
    </div>
  );
}

export default Products;
