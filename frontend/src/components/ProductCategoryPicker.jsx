import { useState, useEffect, useMemo } from 'react';
import { FaSearch, FaTimes, FaCheck } from 'react-icons/fa';
import { getProducts, getCategories } from '../api/services';

function flattenCategories(tree, level = 0) {
  const flat = [];
  tree.forEach(cat => {
    flat.push({ ...cat, level });
    if (cat.children && cat.children.length > 0) {
      flat.push(...flattenCategories(cat.children, level + 1));
    }
  });
  return flat;
}

function ProductCategoryPicker({ scopeType, scopeIds, onChange }) {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [prodData, catData] = await Promise.all([
          getProducts({ limit: 500, is_active: true }),
          getCategories(),
        ]);
        setProducts(prodData.products || []);
        const tree = catData.categories || [];
        setCategories(flattenCategories(tree));
      } catch (err) {
        console.error('Failed to load products/categories', err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const categoryMap = useMemo(() => {
    const map = {};
    categories.forEach(cat => {
      map[cat.id] = cat;
    });
    return map;
  }, [categories]);

  const items = scopeType === 'product' ? products : categories;

  const filtered = items.filter(item => {
    if (scopeType === 'product') {
      if (categoryFilter && String(item.category_id) !== String(categoryFilter)) {
        return false;
      }
    }
    if (!search) return true;
    const q = search.toLowerCase();
    const code = item.product_code || item.code || '';
    return item.name.toLowerCase().includes(q) || (code && code.toLowerCase().includes(q));
  });

  const toggle = (id) => {
    const current = scopeIds || [];
    const updated = current.includes(id)
      ? current.filter(x => x !== id)
      : [...current, id];
    onChange(updated);
  };

  const clearAll = () => {
    onChange([]);
  };

  const clearCategoryFilter = () => {
    setCategoryFilter('');
    setSearch('');
  };

  const selectedItems = items.filter(item => scopeIds.includes(item.id));

  return (
    <div className="product-category-picker">
      <div className="pcp-header">
        <h4>{scopeType === 'product' ? 'Select Products' : 'Select Categories'}</h4>
        {scopeIds.length > 0 && (
          <button type="button" className="pcp-clear-all" onClick={clearAll}>
            Clear All
          </button>
        )}
      </div>

      <div className="pcp-search-container">
        {scopeType === 'product' && (
          <div className="pcp-category-filter">
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="pcp-category-select"
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>
                  {'  '.repeat(cat.level)}{cat.name}
                </option>
              ))}
            </select>
            {categoryFilter && (
              <button
                type="button"
                className="pcp-filter-clear"
                onClick={clearCategoryFilter}
                title="Clear category filter"
              >
                <FaTimes size={10} />
              </button>
            )}
          </div>
        )}

        <div className="pcp-search">
          <FaSearch className="pcp-search-icon" />
          <input
            type="text"
            placeholder={scopeType === 'product' ? 'Search by product name or code...' : 'Search categories...'}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pcp-search-input"
          />
          {search && (
            <button type="button" className="pcp-search-clear" onClick={() => setSearch('')}>
              <FaTimes />
            </button>
          )}
        </div>
      </div>

      <div className="pcp-list">
        {loading ? (
          <p className="pcp-loading">Loading...</p>
        ) : filtered.length === 0 ? (
          <p className="pcp-no-results">No results found</p>
        ) : (
          filtered.map(item => {
            const isSelected = scopeIds.includes(item.id);
            const category = scopeType === 'product' && item.category_id ? categoryMap[item.category_id] : null;
            return (
              <label
                key={item.id}
                className={`pcp-item ${isSelected ? 'selected' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => toggle(item.id)}
                />
                <span className="pcp-item-name">{item.name}</span>
                {item.product_code && !item.code && (
                  <span className="pcp-item-code">{item.product_code}</span>
                )}
                {item.code && (
                  <span className="pcp-item-code">{item.code}</span>
                )}
                {category && (
                  <span className="pcp-item-category" title={category.name}>
                    {category.name}
                  </span>
                )}
                {isSelected && <FaCheck className="pcp-check-icon" />}
              </label>
            );
          })
        )}
      </div>

      {selectedItems.length > 0 && (
        <div className="pcp-selected">
          <div className="pcp-selected-header">
            <span>Selected ({selectedItems.length})</span>
          </div>
          <div className="pcp-selected-tags">
            {selectedItems.map(item => (
              <span key={item.id} className="pcp-tag">
                <span className="pcp-tag-name">{item.name}</span>
                {(item.product_code || item.code) && (
                  <span className="pcp-tag-code">{item.product_code || item.code}</span>
                )}
                <button
                  type="button"
                  className="pcp-tag-remove"
                  onClick={() => toggle(item.id)}
                >
                  <FaTimes />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ProductCategoryPicker;
