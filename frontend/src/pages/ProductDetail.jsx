import { useEffect, useRef, useState } from 'react';
import { FaBolt, FaCheckCircle, FaEye, FaGift, FaPhone, FaShieldAlt, FaShoppingCart, FaTag, FaTruck, FaUndo, FaWhatsapp } from 'react-icons/fa';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { findVariant, getDefaultVariant, getProductBySlug, getProductDiscounts, registerProductView } from '../api/services';
import { useCart } from '../context/CartContext';
import { useDirectBuy } from '../context/DirectBuyContext';
import { useSiteSettings } from '../context/SiteSettingsContext';
import { useToast } from '../context/ToastContext';

function ProductDetail () {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { addItem } = useCart();
  const { setDirectItem } = useDirectBuy();
  const { addToast } = useToast();
  const { settings } = useSiteSettings();
  const [ product, setProduct ] = useState( null );
  const [ loading, setLoading ] = useState( true );
  const [ quantity, setQuantity ] = useState( 1 );
  const [ selectedOptions, setSelectedOptions ] = useState( {} );
  const [ activeImage, setActiveImage ] = useState( 0 );
  const [ added, setAdded ] = useState( false );
  const [ currentVariant, setCurrentVariant ] = useState( null );
  const [ variantLoading, setVariantLoading ] = useState( false );
  const [ variantError, setVariantError ] = useState( null );
  const [ discountInfo, setDiscountInfo ] = useState( null );
  const [ viewersCount, setViewersCount ] = useState( 0 );
  const [ activeTab, setActiveTab ] = useState( 'description' );
  const pageRef = useRef( null );
  const sessionIdRef = useRef( null );

  useEffect( () => {
    const loadProduct = async () => {
      try {
        setLoading( true );
        const data = await getProductBySlug( slug );
        setProduct( data.product );
        setSelectedOptions( {} );
        setCurrentVariant( null );
        setVariantError( null );
        setDiscountInfo( null );

        // Auto-load default variant (preferably in-stock)
        try {
          const variantData = await getDefaultVariant( data.product.id );
          if ( variantData.variant ) {
            setCurrentVariant( variantData.variant );

            // Auto-select the attribute options matching the default variant
            const defaultAttrs = variantData.variant.selected_attributes || {};
            const newSelectedOptions = {};
            ( data.product.attributes || [] ).forEach( ( attr ) => {
              const optionValue = defaultAttrs[ attr.name ];
              if ( optionValue ) {
                const option = attr.options.find( ( opt ) => opt.value === optionValue );
                if ( option ) {
                  newSelectedOptions[ attr.id ] = option.id;
                }
              }
            } );
            if ( Object.keys( newSelectedOptions ).length > 0 ) {
              setSelectedOptions( newSelectedOptions );
            }
          }
        } catch {
          // No variant available, keep null
        }
      } catch ( err ) {
        addToast( err.response?.data?.detail || 'Product not found', 'error' );
      } finally {
        setLoading( false );
      }
    };
    loadProduct();
  }, [ slug ] );

  // Find variant when all attributes are selected
  useEffect( () => {
    if ( !product ) return;

    const attributes = product.attributes || [];

    // If no attributes, just get the single variant
    if ( attributes.length === 0 ) {
      let cancelled = false;
      const loadSingleVariant = async () => {
        setVariantLoading( true );
        try {
          const data = await findVariant( product.id, {} );
          if ( !cancelled ) {
            setCurrentVariant( data.variant );
          }
        } catch ( err ) {
          if ( !cancelled ) {
            setCurrentVariant( null );
            setVariantError( err.response?.data?.detail || 'Variant not available.' );
          }
        } finally {
          if ( !cancelled ) {
            setVariantLoading( false );
          }
        }
      };
      loadSingleVariant();
      return () => { cancelled = true; };
    }

    const allSelected = attributes.every( ( attr ) => selectedOptions[ attr.id ] );

    if ( !allSelected ) {
      return;
    }

    let cancelled = false;

    const findVariantForSelection = async () => {
      setVariantLoading( true );
      setVariantError( null );
      try {
        // Build selected attributes with names as keys
        const selectedAttrs = {};
        attributes.forEach( ( attr ) => {
          const optionId = selectedOptions[ attr.id ];
          const option = attr.options.find( ( opt ) => opt.id === optionId );
          if ( option ) {
            selectedAttrs[ attr.name ] = option.value;
          }
        } );

        const data = await findVariant( product.id, selectedAttrs );
        if ( !cancelled ) {
          setCurrentVariant( data.variant );
        }
      } catch ( err ) {
        if ( !cancelled ) {
          setCurrentVariant( null );
          setVariantError( err.response?.data?.detail || 'Variant not available.' );
        }
      } finally {
        if ( !cancelled ) {
          setVariantLoading( false );
        }
      }
    };

    findVariantForSelection();

    return () => {
      cancelled = true;
    };
  }, [ product, selectedOptions ] );

  // Refetch discount info whenever the product or selected variant changes
  useEffect( () => {
    if ( !product ) return;
    const unitPrice = currentVariant?.price
      ? parseFloat( currentVariant.price )
      : ( product.price_range ? parseFloat( product.price_range.min ) : 0 );
    let cancelled = false;
    getProductDiscounts( product.id, unitPrice )
      .then( ( discData ) => {
        if ( !cancelled && discData?.discount_info ) {
          setDiscountInfo( discData.discount_info );
        }
      } )
      .catch( () => { } );
    return () => { cancelled = true; };
  }, [ product, currentVariant ] );

  // Real-time viewer count: register a session on mount and poll periodically.
  // Session ID is persisted in sessionStorage so page refreshes reuse the
  // same session (no duplicate counting), while new tabs get their own ID.
  useEffect( () => {
    if ( !product ) return;

    const storageKey = `wave_viewer_sid`;
    let sid = sessionStorage.getItem( storageKey );
    if ( !sid ) {
      sid = `viewer_${ Date.now() }_${ Math.random().toString( 36 ).slice( 2, 11 ) }`;
      sessionStorage.setItem( storageKey, sid );
    }
    sessionIdRef.current = sid;

    const refreshView = async () => {
      try {
        const data = await registerProductView( product.id, sid );
        if ( data?.count != null ) {
          setViewersCount( data.count );
        }
      } catch {
        // Silently fail — view count is non-critical
      }
    };

    refreshView();
    const interval = setInterval( refreshView, 5000 );

    return () => clearInterval( interval );
  }, [ product ] );

  const handleOptionSelect = ( attributeId, optionId ) => {
    setSelectedOptions( ( prev ) => ( {
      ...prev,
      [ attributeId ]: optionId,
    } ) );
  };

  // Check if every attribute has a selected option
  const missingAttributes = ( product?.attributes || [] ).filter(
    ( attr ) => !selectedOptions[ attr.id ]
  );

  const allSelected = missingAttributes.length === 0;
  const variantInStock = currentVariant?.in_stock && currentVariant?.stock_quantity > 0;
  const maxQuantity = currentVariant?.stock_quantity || 0;

  const handleBuyNow = async () => {
    if ( !allSelected ) {
      addToast( 'Please select all options before buying.', 'error' );
      return;
    }

    if ( !currentVariant || !variantInStock ) {
      addToast( 'This variant is out of stock.', 'error' );
      return;
    }

    if ( quantity > maxQuantity ) {
      addToast( `Only ${ maxQuantity } item(s) available in stock.`, 'error' );
      return;
    }

    const selectedAttrs = {};
    product.attributes?.forEach( ( attr ) => {
      const selectedOptionId = selectedOptions[ attr.id ];
      if ( selectedOptionId ) {
        selectedAttrs[ attr.id ] = selectedOptionId;
      }
    } );
    const attrsString = Object.keys( selectedAttrs ).length > 0
      ? JSON.stringify( selectedAttrs )
      : null;
    setDirectItem( { product, selectedOptions, quantity, attrsString, variant: currentVariant } );
    navigate( '/checkout' );
  };

  const handleAddToCart = async () => {
    if ( !allSelected ) {
      addToast( 'Please select all options before adding to cart.', 'error' );
      return;
    }

    if ( !currentVariant || !variantInStock ) {
      addToast( 'This variant is out of stock.', 'error' );
      return;
    }

    if ( quantity > maxQuantity ) {
      addToast( `Only ${ maxQuantity } item(s) available in stock.`, 'error' );
      return;
    }

    const selectedAttrs = {};
    product.attributes?.forEach( ( attr ) => {
      const selectedOptionId = selectedOptions[ attr.id ];
      if ( selectedOptionId ) {
        selectedAttrs[ attr.id ] = selectedOptionId;
      }
    } );

    const attrsString = Object.keys( selectedAttrs ).length > 0
      ? JSON.stringify( selectedAttrs )
      : null;

    const result = await addItem( product.id, quantity, attrsString );
    if ( result.success ) {
      setAdded( true );
      setTimeout( () => setAdded( false ), 2000 );
      triggerFlyToCart( pageRef.current );
      addToast( 'Added to cart!', 'success' );
    } else {
      addToast( result.error || 'Failed to add to cart.', 'error' );
    }
  };

  if ( loading ) {
    return <div className="container loading">Loading product...</div>;
  }

  if ( !product ) {
    return (
      <div className="container empty-state">
        <h3>Product not found</h3>
        <Link to="/products" className="btn btn-primary">Back to Products</Link>
      </div>
    );
  }

  const validFiles = ( product.files || [] ).filter( ( f ) => f.file_url );
  const images = validFiles.length > 0 ? validFiles : [ { file_url: 'https://placehold.co/500x500?text=No+Image' } ];

  // Display price: exact variant price if selected, otherwise price range
  const displayPrice = currentVariant?.price
    ? parseFloat( currentVariant.price )
    : null;
  const priceRange = product.price_range;
  const rangeMin = priceRange ? parseFloat( priceRange.min ) : null;
  const rangeMax = priceRange ? parseFloat( priceRange.max ) : null;
  const showRange = !displayPrice && rangeMin != null && rangeMax != null && rangeMin !== rangeMax;
  const discountRange = discountInfo?.discounted_price_range;
  const originalRange = discountInfo?.original_price_range;
  const hasDiscountRange = !!showRange && !!discountRange &&
    parseFloat( discountRange.min ) !== parseFloat( discountRange.max );
  const fmt = ( v ) => Number( v ).toLocaleString();

  return (
    <div className="product-detail-page" ref={ pageRef }>
      <div className="container">
        {/* Breadcrumb */ }
        <nav className="breadcrumb">
          <Link to="/">Home</Link> / <Link to="/products">Products</Link> / <span>{ product.name }</span>
        </nav>

        <div className="product-detail-grid">
          {/* Images */ }
          <div className="product-images">
            <div className="main-image">
              <img src={ images[ activeImage ]?.file_url } alt={ product.name } />
            </div>
            { images.length > 1 && (
              <div className="thumbnail-list">
                { images.map( ( img, index ) => (
                  <button
                    key={ img.id || index }
                    className={ `thumbnail ${ index === activeImage ? 'active' : '' }` }
                    onClick={ () => setActiveImage( index ) }
                    aria-label={ `View image ${ index + 1 }` }
                  >
                    <img src={ img.file_url } alt={ `${ product.name } ${ index + 1 }` } />
                  </button>
                ) ) }
              </div>
            ) }
          </div>

          {/* Product Info */ }
          <div className="product-info-detail">
            <h1 className="product-title">{ product.name }</h1>
            <p className="product-code">Product Code: { product.product_code }</p>

            <div className="viewer-count">
              <FaEye className="viewer-count-icon" />
              <span>{ viewersCount } { viewersCount === 1 ? 'person' : 'people' } viewing this product right now</span>
            </div>

            <div className="product-price-detail">
              { hasDiscountRange ? (
                <>
                  <span className="price-original">৳{ fmt( originalRange?.min ) } - ৳{ fmt( originalRange?.max ) }</span>
                  <span className="price-discounted">৳{ fmt( discountRange.min ) } - ৳{ fmt( discountRange.max ) }</span>
                </>
              ) : discountInfo?.discounted_price ? (
                <>
                  <span className="price-original">৳{ fmt( discountInfo.original_price || displayPrice ) }</span>
                  <span className="price-discounted">৳{ fmt( discountInfo.discounted_price ) }</span>
                </>
              ) : displayPrice ? (
                <span className="price">৳{ fmt( displayPrice ) }</span>
              ) : showRange ? (
                <span className="price">৳{ fmt( rangeMin ) } - ৳{ fmt( rangeMax ) }</span>
              ) : (
                <span className="price">৳0</span>
              ) }
              { discountInfo?.free_shipping && (
                <span className="shipping-badge-detail">🚚 Free Shipping</span>
              ) }
            </div>

            { discountInfo?.badge && (
              <span className={ `product-badge badge-${ discountInfo.badge_type === 'free_shipping' ? 'success' : 'danger' }` }>
                { discountInfo.badge }
              </span>
            ) }

            {/* Quantity Bundle Offer Info Box */ }
            { discountInfo?.bundle_slabs_info && discountInfo.bundle_slabs_info.length > 0 && (
              <div className="offer-info-box">
                <h4><FaTag /> Offer Terms</h4>
                <ul className="offer-slabs-list">
                  { discountInfo.bundle_slabs_info.map( ( bundle, bIdx ) => (
                    <li key={ bIdx } className="offer-slab-group">
                      <span className="offer-discount-name">{ bundle.discount_name }</span>
                      { bundle.slabs.map( ( slab ) => (
                        <span key={ slab.min_quantity } className="offer-slab-item">
                          { slab.min_quantity } items for{ ' ' }
                          { slab.value_type === 'percentage'
                            ? `${ parseInt( slab.value ) }% OFF`
                            : `৳${ parseInt( slab.value ) } OFF` }
                          { bundle.free_shipping && <span className="offer-fs-inline"> + Free Shipping</span> }
                        </span>
                      ) ) }
                    </li>
                  ) ) }
                </ul>
              </div>
            ) }

            {/* Combo Bundle Section */ }
            { discountInfo?.combo_products && discountInfo.combo_products.length > 0 && (
              <div className="combo-bundle-section">
                <h4><FaGift /> Also Buy</h4>
                <div className="combo-products-list">
                  { discountInfo.combo_products.map( ( cp ) => (
                    <Link
                      key={ cp.id }
                      to={ `/product/${ cp.slug }` }
                      className="combo-product-link"
                    >
                      { cp.name }
                    </Link>
                  ) ) }
                </div>
              </div>
            ) }

            <div className="stock-badge-row">
              { allSelected && currentVariant ? (
                variantInStock ? (
                  <span className="stock-badge in-stock">
                    ✓ In Stock{ maxQuantity > 0 ? ` (${ maxQuantity } in stock)` : '' }
                  </span>
                ) : (
                  <span className="stock-badge out-of-stock">✗ Out of Stock</span>
                )
              ) : variantError ? (
                <span className="stock-badge out-of-stock">✗ { variantError }</span>
              ) : (
                <span className="stock-badge in-stock">✓ In Stock</span>
              ) }
            </div>

            {/* Attributes - no auto-selection, user must choose */ }
            { product.attributes?.length > 0 && (
              <div className="attributes-section">
                { product.attributes.map( ( attr ) => {
                  const isSelected = !!selectedOptions[ attr.id ];
                  return (
                    <div className="attribute-group" key={ attr.id }>
                      <h4 className="attribute-name">
                        { attr.name }:
                        { !isSelected && <span className="attribute-required"> *</span> }
                      </h4>
                      <div className="attribute-options">
                        { attr.options.map( ( option ) => (
                          <button
                            key={ option.id }
                            className={ `attribute-option-btn ${ selectedOptions[ attr.id ] === option.id ? 'selected' : ''
                              }` }
                            onClick={ () => handleOptionSelect( attr.id, option.id ) }
                          >
                            { option.value }
                          </button>
                        ) ) }
                      </div>
                      { !isSelected && (
                        <p className="attribute-missing-hint">Please select { attr.name.toLowerCase() } to continue.</p>
                      ) }
                    </div>
                  );
                } ) }
              </div>
            ) }

            {/* Quantity */ }
            <div className="quantity-section">
              <h4>Quantity:</h4>
              <div className="quantity-control">
                <button
                  onClick={ () => setQuantity( ( q ) => Math.max( 1, q - 1 ) ) }
                  aria-label="Decrease quantity"
                >
                  -
                </button>
                <span>{ quantity }</span>
                <button
                  onClick={ () => setQuantity( ( q ) => Math.min( q + 1, maxQuantity || 1 ) ) }
                  disabled={ allSelected && currentVariant && ( quantity >= maxQuantity || !variantInStock ) }
                  aria-label="Increase quantity"
                >
                  +
                </button>
              </div>
              { allSelected && currentVariant && !variantInStock && (
                <p className="stock-warning">Out of stock</p>
              ) }
            </div>

            {/* Action Buttons Grid */ }
            <div className="action-buttons-grid">
              {/* Add to Cart */ }
              <button
                className="btn btn-primary btn-lg add-to-cart-detail"
                onClick={ handleAddToCart }
                disabled={ !allSelected || !currentVariant || !variantInStock || variantLoading || quantity > maxQuantity }
              >
                { added ? <><FaCheckCircle /> Added to Cart</> : <><FaShoppingCart /> Add to Cart</> }
              </button>

              {/* Buy Now */ }
              <button
                className="btn btn-success btn-lg add-to-cart-detail"
                onClick={ handleBuyNow }
                disabled={ !allSelected || !currentVariant || !variantInStock || variantLoading || quantity > maxQuantity }
              >
                <FaBolt /> Buy Now
              </button>

              {/* Order via WhatsApp / Call */ }
              { ( settings?.order_whatsapp_number || settings?.order_call_number ) && (
                <div className="order-contact-buttons">
                  { settings?.order_whatsapp_number && (
                    <a
                      className="order-contact-btn order-whatsapp-btn"
                      href={ `https://wa.me/${ settings.order_whatsapp_number.replace( /[^0-9]/g, '' ) }?text=${ encodeURIComponent( `Hi, I want to order: ${ product.name } (Code: ${ product.product_code })` ) }` }
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <FaWhatsapp /> Order on WhatsApp
                    </a>
                  ) }
                  { settings?.order_call_number && (
                    <a
                      className="order-contact-btn order-call-btn"
                      href={ `tel:${ settings.order_call_number.replace( /[^0-9]/g, '' ) }` }
                    >
                      <FaPhone /> Call for Order: { settings.order_call_number }
                    </a>
                  ) }
                </div>
              ) }
            </div>

            {/* Trust badges */ }
            <div className="trust-badges">
              <div className="trust-item">
                <FaTruck />
                <span>Fast Delivery</span>
              </div>
              <div className="trust-item">
                <FaShieldAlt />
                <span>Quality Guarantee</span>
              </div>
              <div className="trust-item">
                <FaUndo />
                <span>Easy Returns</span>
              </div>
            </div>
          </div>
        </div>

        {/* Description / Additional Information Tabs */ }
        <div className="product-description">
          <div className="product-tabs">
            <button
              className={ `tab-btn ${ activeTab === 'description' ? 'active' : '' }` }
              onClick={ () => setActiveTab( 'description' ) }
            >
              Description
            </button>
            <button
              className={ `tab-btn ${ activeTab === 'specification' ? 'active' : '' }` }
              onClick={ () => setActiveTab( 'specification' ) }
            >
              Additional Information
            </button>
          </div>

          <div className="tab-content">
            { activeTab === 'description' && (
              <div className="tab-pane">
                <p>{ product.description || 'No description available.' }</p>
              </div>
            ) }
            { activeTab === 'specification' && (
              <div className="tab-pane">
                { product.specifications ? (
                  <p>{ product.specifications }</p>
                ) : (
                  <p>No specifications available.</p>
                ) }
              </div>
            ) }
          </div>
        </div>
      </div>
    </div>
  );
}

// Fly-to-cart animation: creates a flying item that animates from the card to the cart icon
function triggerFlyToCart ( sourceEl ) {
  if ( !sourceEl ) return;
  const cartBtn = document.querySelector( '.cart-btn' );
  if ( !cartBtn ) return;

  const sourceRect = sourceEl.getBoundingClientRect();
  const cartRect = cartBtn.getBoundingClientRect();

  const startX = sourceRect.left + sourceRect.width / 2;
  const startY = sourceRect.top + sourceRect.height / 2;
  const endX = cartRect.left + cartRect.width / 2;
  const endY = cartRect.top + cartRect.height / 2;

  const deltaX = endX - startX;
  const deltaY = endY - startY;

  // Get the product image to fly
  const productImg = sourceEl.querySelector( '.main-image img, .product-main-image, .product-image, .product-detail-image' );
  const imgSrc = productImg ? productImg.src : null;

  const flyEl = document.createElement( 'div' );
  flyEl.className = 'fly-to-cart';
  if ( imgSrc ) {
    const img = document.createElement( 'img' );
    img.src = imgSrc;
    img.alt = '';
    img.style.cssText = 'width:100%;height:100%;object-fit:cover;border-radius:50%;';
    flyEl.appendChild( img );
  } else {
    flyEl.textContent = '🛒';
  }
  document.body.appendChild( flyEl );

  flyEl.style.left = `${ startX }px`;
  flyEl.style.top = `${ startY }px`;
  flyEl.style.setProperty( '--fly-to-x', `${ deltaX }px` );
  flyEl.style.setProperty( '--fly-to-y', `${ deltaY }px` );
  flyEl.style.animation = 'fly-to-cart-parabolic 0.9s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards';

  // Create sparkles with alternating colors
  for ( let i = 0; i < 8; i++ ) {
    const sparkle = document.createElement( 'div' );
    sparkle.className = 'cart-sparkle';
    sparkle.style.left = `${ startX }px`;
    sparkle.style.top = `${ startY }px`;
    sparkle.style.animationDelay = `${ i * 0.06 }s`;
    sparkle.style.setProperty( '--sparkle-rotation', `${ i * 45 }deg` );
    document.body.appendChild( sparkle );
  }

  setTimeout( () => {
    flyEl.remove();
    document.querySelectorAll( '.cart-sparkle' ).forEach( ( el ) => el.remove() );
    cartBtn.classList.add( 'cart-bounce' );
    setTimeout( () => cartBtn.classList.remove( 'cart-bounce' ), 600 );
  }, 900 );
}

export default ProductDetail;