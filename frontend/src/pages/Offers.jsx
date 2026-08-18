import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FaTag, FaGift, FaTruck, FaShoppingCart } from 'react-icons/fa';
import { getOffers } from '../api/services';
import { useToast } from '../context/ToastContext';

function Offers() {
  const { addToast } = useToast();
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeType, setActiveType] = useState('all');

  const offerTypes = [
    { value: 'all', label: 'All Offers' },
    { value: 'percentage', label: 'Percentage Off' },
    { value: 'flat', label: 'Flat Discount' },
    { value: 'bundle', label: 'Bundles' },
    { value: 'bogo', label: 'BOGO' },
    { value: 'free_shipping', label: 'Free Shipping' },
  ];

  const loadOffers = async (type = null) => {
    try {
      setLoading(true);
      const params = {};
      if (type && type !== 'all') {
        params.discount_type = type;
      }
      const data = await getOffers(params);
      setOffers(data.offers || []);
    } catch (err) {
      console.error('Failed to load offers:', err);
      addToast('Failed to load offers.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOffers(activeType !== 'all' ? activeType : null);
  }, [activeType]);

  const handleTypeClick = (typeValue) => {
    setActiveType(typeValue);
  };

  const getBadgeIcon = (type) => {
    switch (type) {
      case 'percentage':
      case 'flat':
        return <FaTag />;
      case 'bundle':
        return <FaShoppingCart />;
      case 'bogo':
        return <FaGift />;
      case 'free_shipping':
        return <FaTruck />;
      default:
        return <FaTag />;
    }
  };

  const getOfferLink = (offer) => {
    if (offer.scopes && offer.scopes.length > 0) {
      const scope = offer.scopes[0];
      if (scope.scope_type === 'product' && scope.scope_id) {
        return null;
      }
      if (scope.scope_type === 'category' && scope.scope_id) {
        return `/products?category=${scope.scope_id}`;
      }
    }
    if (offer.bogo_rule && offer.bogo_rule.product_slug) {
      return `/product/${offer.bogo_rule.product_slug}`;
    }
    if (offer.bundle_rule && offer.bundle_rule.required_products && offer.bundle_rule.required_products.length > 0) {
      return `/product/${offer.bundle_rule.required_products[0].slug}`;
    }
    return null;
  };

  if (loading) {
    return (
      <div className="container loading">
        <div className="loading-spinner"></div>
        <p>Loading offers...</p>
      </div>
    );
  }

  return (
    <div className="offers-page">
      <div className="container">
        <div className="page-header">
          <h1>Special Offers</h1>
          <p>Exclusive deals and discounts just for you</p>
        </div>

        {/* Type filter */}
        <div className="offers-filter">
          {offerTypes.map((type) => (
            <button
              key={type.value}
              className={`offer-type-btn ${activeType === type.value ? 'active' : ''}`}
              onClick={() => handleTypeClick(type.value)}
            >
              {type.label}
            </button>
          ))}
        </div>

        {offers.length === 0 ? (
          <div className="empty-state">
            <FaTag className="empty-icon" />
            <h3>No offers available</h3>
            <p>Check back later for new deals!</p>
          </div>
        ) : (
          <div className="offers-grid">
            {offers.map((offer) => {
              const link = getOfferLink(offer);
              const badgeClass =
                offer.badge_type === 'free_shipping'
                  ? 'badge-success'
                  : offer.badge_type === 'bogo'
                    ? 'badge-warning'
                    : 'badge-danger';

              const cardContent = (
                <>
                  <div className="offer-card-header">
                    <span className={`offer-badge ${badgeClass}`}>
                      {getBadgeIcon(offer.type)}
                      {offer.badge_text || offer.name}
                    </span>
                    {offer.end_date && (
                      <span className="offer-end-date">
                        Ends: {new Date(offer.end_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>

                  <h3 className="offer-name">{offer.name}</h3>

                  {offer.scopes && offer.scopes.length > 0 && (
                    <div className="offer-scopes">
                      {offer.scopes.map((scope, idx) => (
                        <span key={idx} className="offer-scope-tag">
                          {scope.scope_type === 'product' ? '📦 Product' : '📁 Category'}: {scope.scope_name}
                        </span>
                      ))}
                    </div>
                  )}

                  {offer.bundle_rule && offer.bundle_rule.bundle_type === 'quantity' && offer.bundle_rule.slabs && offer.bundle_rule.slabs.length > 0 && (
                    <div className="offer-slabs-preview">
                      {offer.bundle_rule.slabs.map((slab) => (
                        <div key={slab.min_quantity} className="offer-slab-row">
                          <span className="slab-min-qty">{slab.min_quantity}+</span>
                          <span className="slab-value">
                            {slab.value_type === 'percentage'
                              ? `${parseInt(slab.value)}% OFF`
                              : `৳${parseInt(slab.value)} OFF`}
                          </span>
                        </div>
                      ))}
                      {(offer.free_shipping || offer.bundle_rule?.free_shipping) && (
                        <span className="offer-fs-tag">🚚 Free Shipping</span>
                      )}
                    </div>
                  )}

                  {offer.bogo_rule && (
                    <div className="offer-bogo-preview">
                      <span className="bogo-text">
                        Buy {offer.bogo_rule.buy_quantity} Get {offer.bogo_rule.get_quantity}
                      </span>
                      <span className="bogo-discount">
                        ({parseInt(offer.bogo_rule.get_discount_percent)}% off)
                      </span>
                    </div>
                  )}

                  {offer.discount_breakdown && (
                    <div className="offer-meta">
                      <span className={`offer-badge-type ${badgeClass}-bg`}>
                        {offer.type}
                      </span>
                    </div>
                  )}
                </>
              );

              if (link) {
                return (
                  <Link key={offer.id} to={link} className="offer-card-link">
                    <div className="offer-card">
                      {cardContent}
                    </div>
                  </Link>
                );
              }

              return (
                <div key={offer.id} className="offer-card">
                  {cardContent}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default Offers;
