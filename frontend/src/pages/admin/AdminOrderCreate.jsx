import { useEffect, useState } from 'react';
import { FaArrowLeft, FaPlus, FaSave, FaTrash } from 'react-icons/fa';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { adminCreateOrder, adminGetOrder, adminGetProduct, adminGetProducts, adminUpdateOrder, adminCalculateOrderPreview } from '../../api/adminServices';
import { findVariant, getDistricts } from '../../api/services';
import PhoneInput from '../../components/PhoneInput';
import { useToast } from '../../context/ToastContext';

function AdminOrderCreate () {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditing = Boolean( id );
  const { addToast } = useToast();
  const [ products, setProducts ] = useState( [] );
  const [ loading, setLoading ] = useState( Boolean( id ) );
  const [ districts, setDistricts ] = useState( [] );
  const [ customer, setCustomer ] = useState( { full_name: '', phone_number: '+880', district: '', thana: '', note: '', address: '' } );
  const [ items, setItems ] = useState( [] );
  const [ selectedProductId, setSelectedProductId ] = useState( '' );
  const [ saving, setSaving ] = useState( false );
  const [ productCache, setProductCache ] = useState( {} );
  const [ preview, setPreview ] = useState( null );
  const [ previewLoading, setPreviewLoading ] = useState( false );

  // Load products and districts
  useEffect( () => {
    const loadData = async () => {
      try {
        const [ pData, dData ] = await Promise.all( [
          adminGetProducts( { limit: 100, is_active: true } ),
          getDistricts(),
        ] );
        setProducts( pData.products || [] );
        setDistricts( dData.districts || [] );
      } catch {
        addToast( 'Failed to load data.', 'error' );
      }
    };
    loadData();
  }, [] );

  // Preview discounts when items change
  useEffect( () => {
    if ( items.length === 0 ) {
      setPreview( null );
      return;
    }
    const timer = setTimeout( async () => {
      setPreviewLoading( true );
      try {
        const payloadItems = items.map( ( it ) => ( {
          product_id: it.product_id,
          quantity: it.quantity,
          selected_attributes: Object.keys( it.selected_options || {} ).length > 0
            ? JSON.stringify( it.selected_options )
            : null,
        } ) );
        const data = await adminCalculateOrderPreview( payloadItems );
        setPreview( data );
      } catch {
        // silently ignore preview errors
      } finally {
        setPreviewLoading( false );
      }
    }, 300 );
    return () => clearTimeout( timer );
  }, [ items ] );

  // Load full product detail (with attributes/options) when needed
  const loadProductDetail = async ( pid ) => {
    if ( productCache[ pid ] ) return productCache[ pid ];
    try {
      const data = await adminGetProduct( pid );
      const prod = data.product;
      setProductCache( ( prev ) => ( { ...prev, [ pid ]: prod } ) );
      return prod;
    } catch {
      return null;
    }
  };

  const resolveItemVariant = async ( item ) => {
    if ( !item.attributes || item.attributes.length === 0 ) {
      try {
        const data = await findVariant( item.product_id, {} );
        return { price: data.variant?.price || null, stock_quantity: data.variant?.stock_quantity ?? 0 };
      } catch {
        return { price: null, stock_quantity: 0 };
      }
    }
    const selectedOptions = item.selected_options || {};
    const allSelected = item.attributes.every( ( attr ) => selectedOptions[ attr.id ] );
    if ( !allSelected ) return { price: null, stock_quantity: 0 };

    const selectedAttrs = {};
    for ( const [ attrId, optId ] of Object.entries( selectedOptions ) ) {
      const attr = item.attributes.find( ( a ) => String( a.id ) === String( attrId ) );
      if ( attr ) {
        const option = ( attr.options || [] ).find( ( o ) => o.id === optId );
        if ( option ) {
          selectedAttrs[ attr.name ] = option.value;
        }
      }
    }

    if ( Object.keys( selectedAttrs ).length === 0 ) return { price: null, stock_quantity: 0 };

    try {
      const data = await findVariant( item.product_id, selectedAttrs );
      return { price: data.variant?.price || null, stock_quantity: data.variant?.stock_quantity ?? 0 };
    } catch {
      return { price: null, stock_quantity: 0 };
    }
  };

  const handleOptionChange = async ( index, attrId, optionId ) => {
    const newItems = [ ...items ];
    const selected_options = { ...newItems[ index ].selected_options, [ attrId ]: optionId };
    newItems[ index ] = { ...newItems[ index ], selected_options, unit_price: undefined, stock_quantity: undefined };
    setItems( newItems );

    const { price, stock_quantity } = await resolveItemVariant( newItems[ index ] );
    if ( price !== null ) {
      setItems( ( prev ) => prev.map( ( it, i ) => ( i === index ? { ...it, unit_price: price, stock_quantity } : it ) ) );
    }
  };

  const handleResetOptions = ( index ) => {
    setItems( ( prev ) => prev.map( ( it, i ) => ( i === index ? { ...it, selected_options: {}, unit_price: undefined } : it ) ) );
  };

  // Load existing order when editing - show items immediately
  useEffect( () => {
    if ( !isEditing ) return;
    const loadOrder = async () => {
      try {
        setLoading( true );
        const data = await adminGetOrder( id );
        const order = data.order;
        setCustomer( {
          full_name: order.full_name || '',
          phone_number: order.phone_number || '',
          district: order.district || '',
          thana: order.thana || '',
          note: order.note || '',
          address: order.address || '',
        } );

        // Build items immediately from order data - use snapshot prices as fallback
        const baseItems = ( order.items || [] ).map( ( item ) => {
          let selected_options = {};
          if ( item.selected_attributes ) {
            try {
              selected_options = JSON.parse( item.selected_attributes );
            } catch {
              selected_options = {};
            }
          }
          return {
            product_id: item.product_id,
            product_name: item.product_name || `Product #${ item.product_id }`,
            quantity: item.quantity,
            bonus_quantity: item.bonus_quantity || 0,
            price_at_purchase: item.price_at_purchase !== undefined ? parseFloat( item.price_at_purchase ) : undefined,
            selected_options,
            attributes: [],
            unit_price: item.unit_price !== undefined ? parseFloat( item.unit_price ) : undefined,
            stock_quantity: undefined,
          };
        } );
        setItems( baseItems );

        // Then asynchronously load product attributes for each item
        // If product is deleted, keep using the snapshot price
        for ( const item of baseItems ) {
          if ( item.product_id === null || item.product_id === undefined ) {
            continue; // Product deleted - keep snapshot data as-is
          }
          try {
            const detail = await loadProductDetail( item.product_id );
            if ( detail?.attributes ) {
              setItems( ( prev ) => prev.map( ( it ) =>
                it.product_id === item.product_id ? { ...it, attributes: detail.attributes } : it
              ) );
              // Resolve variant price and stock for this item - only override if successfully resolved
              const { price, stock_quantity } = await resolveItemVariant( { ...item, attributes: detail.attributes } );
              if ( price !== null && price !== undefined && price > 0 ) {
                setItems( ( prev ) => prev.map( ( it ) =>
                  it.product_id === item.product_id ? { ...it, unit_price: price, stock_quantity } : it
                ) );
              }
            }
          } catch {
            // Product deleted or failed to load - keep snapshot unit_price
          }
        }
      } catch ( err ) {
        addToast( err.response?.data?.detail || 'Failed to load order.', 'error' );
      } finally {
        setLoading( false );
      }
    };
    loadOrder();
  }, [ id, isEditing ] );

  const handleAddProduct = async () => {
    if ( !selectedProductId ) return;
    const pid = parseInt( selectedProductId );
    const product = products.find( ( p ) => p.id === pid );
    if ( !product ) return;

    const detail = await loadProductDetail( pid );
    const attrs = detail?.attributes || [];
    let unit_price = undefined;
    let stock_quantity = undefined;

    if ( attrs.length === 0 ) {
      const resolved = await resolveItemVariant( { product_id: pid, attributes: [] } );
      if ( resolved.price !== null ) unit_price = resolved.price;
      stock_quantity = resolved.stock_quantity;
    }

    setItems( ( prev ) => [
      ...prev,
      {
        product_id: pid,
        product_name: product.name,
        quantity: 1,
        selected_options: {},
        attributes: attrs,
        unit_price,
        stock_quantity,
      },
    ] );
    setSelectedProductId( '' );
  };

  const handleQuantityChange = ( index, qty ) => {
    const item = items[ index ];
    const maxStock = item.stock_quantity ?? Infinity;
    const clamped = Math.max( 1, Math.min( qty, maxStock ) );
    if ( qty > maxStock ) {
      addToast( `Only ${ maxStock } item(s) available in stock.`, 'error' );
    }
    setItems( ( prev ) => prev.map( ( it, i ) => ( i === index ? { ...it, quantity: clamped } : it ) ) );
  };

  const handleRemoveItem = ( index ) => {
    setItems( ( prev ) => prev.filter( ( _, i ) => i !== index ) );
  };

  const buildPayload = () => {
    const payloadItems = items.map( ( it ) => {
      const selected_attributes = Object.keys( it.selected_options ).length > 0
        ? JSON.stringify( it.selected_options )
        : null;
      return {
        product_id: it.product_id,
        quantity: it.quantity,
        selected_attributes,
      };
    } );
    return {
      full_name: customer.full_name,
      phone_number: customer.phone_number,
      district: customer.district,
      thana: customer.thana,
      note: customer.note || null,
      address: customer.address,
      items: payloadItems,
    };
  };

  const handleSubmit = async ( e ) => {
    e.preventDefault();

    if ( !customer.full_name.trim() ) return addToast( 'Enter customer name.', 'error' );
    if ( !customer.phone_number.trim() || customer.phone_number.trim().length < 11 ) return addToast( 'Enter a valid 11-digit phone number.', 'error' );
    if ( !customer.district ) return addToast( 'Select a district.', 'error' );
    if ( !customer.address.trim() ) return addToast( 'Enter the address.', 'error' );
    if ( items.length === 0 ) return addToast( 'Add at least one product.', 'error' );

    // Validate quantities against available stock
    for ( const item of items ) {
      if ( item.stock_quantity !== undefined && item.stock_quantity !== null && item.quantity > item.stock_quantity ) {
        const prodName = item.product_name || `Product #${ item.product_id }`;
        return addToast( `Quantity for "${ prodName }" exceeds stock (${ item.quantity } > ${ item.stock_quantity }).`, 'error' );
      }
    }

    try {
      setSaving( true );
      const payload = buildPayload();
      const result = isEditing
        ? await adminUpdateOrder( id, payload )
        : await adminCreateOrder( payload );
      navigate( `/admin/orders/${ result.order.id }` );
      addToast( 'Order saved successfully!', 'success' );
    } catch ( err ) {
      addToast( err.response?.data?.detail || 'Failed to save order.', 'error' );
    } finally {
      setSaving( false );
    }
  };

  const calculateItemTotal = ( item ) => {
    if ( item.price_at_purchase !== undefined && item.price_at_purchase !== null ) {
      return parseFloat( item.price_at_purchase );
    }
    if ( preview && preview.items ) {
      const previewItem = preview.items.find( ( pi ) => {
        return pi.product_id === item.product_id && pi.quantity === item.quantity;
      } );
      if ( previewItem && previewItem.discounted_subtotal ) {
        return parseFloat( previewItem.discounted_subtotal );
      }
    }
    const unit = item.unit_price !== undefined ? parseFloat( item.unit_price ) : 0;
    return unit * item.quantity;
  };

  const getItemPreview = ( item ) => {
    if ( !preview || !preview.items ) return null;
    return preview.items.find( ( pi ) => {
      try {
        if ( item.selected_attributes ) {
          JSON.parse( item.selected_attributes );
          let previewAttrs = {};
          try {
            if ( pi.selected_attributes ) {
              previewAttrs = JSON.parse( pi.selected_attributes );
            }
          } catch {
            // ignore
          }
        }
      } catch {
        // ignore
      }
      return pi.product_id === item.product_id && pi.quantity === item.quantity;
    } ) || null;
  };

  const totalPrice = items.reduce( ( sum, it ) => sum + calculateItemTotal( it ), 0 );
  const previewTotal = preview && preview.total_after_discount != null ? parseFloat( preview.total_after_discount ) : totalPrice;

  if ( loading ) return <div className="loading">Loading order...</div>;

  return (
    <div className="admin-page order-create-page">
      <div className="admin-page-header">
        <h2>{ isEditing ? 'Edit Order' : 'Create Order' }</h2>
        <div className="header-actions">
          <Link to="/admin/orders" className="btn btn-secondary">
            <FaArrowLeft /> Back
          </Link>
        </div>
      </div>

      <form onSubmit={ handleSubmit }>
        {/* Customer Info */ }
        <div className="order-detail-card">
          <h3>Customer Information</h3>
          <div className="order-detail-grid">
            <div className="form-group">
              <label>Full Name *</label>
              <input type="text" value={ customer.full_name } onChange={ ( e ) => setCustomer( { ...customer, full_name: e.target.value } ) } placeholder="Customer name" />
            </div>
            <div className="form-group">
              <label>Phone Number *</label>
              <PhoneInput
                value={ customer.phone_number }
                onChange={ ( _, value ) => setCustomer( { ...customer, phone_number: value } ) }
                placeholder="0XXXXXXXXX"
              />
            </div>
            <div className="form-group">
              <label>District *</label>
              <select value={ customer.district } onChange={ ( e ) => setCustomer( { ...customer, district: e.target.value } ) }>
                <option value="">Select District</option>
                { districts.map( ( d ) => <option key={ d } value={ d }>{ d }</option> ) }
              </select>
            </div>
            <div className="form-group">
              <label>Thana *</label>
              <input type="text" value={ customer.thana } onChange={ ( e ) => setCustomer( { ...customer, thana: e.target.value } ) } placeholder="Enter thana" />
            </div>
          </div>
          <div className="form-group">
            <label>Full Address *</label>
            <textarea value={ customer.address } onChange={ ( e ) => setCustomer( { ...customer, address: e.target.value } ) } rows="2" placeholder="House, Road, Area" />
          </div>
          <div className="form-group">
            <label>Note (optional)</label>
            <textarea value={ customer.note } onChange={ ( e ) => setCustomer( { ...customer, note: e.target.value } ) } rows="2" placeholder="Add a short note (optional)" />
          </div>
        </div>

        {/* Add Products */ }
        <div className="order-detail-card">
          <h3>Add Products</h3>
          <div className="product-add-row">
            <select value={ selectedProductId } onChange={ ( e ) => setSelectedProductId( e.target.value ) }>
              <option value="">Select a product...</option>
              { products.map( ( p ) => <option key={ p.id } value={ p.id }>{ p.name } ({ p.price_range ? ( parseFloat( p.price_range.min ) === parseFloat( p.price_range.max ) ? `৳${ parseFloat( p.price_range.min ).toLocaleString() }` : `৳${ parseFloat( p.price_range.min ).toLocaleString() } - ৳${ parseFloat( p.price_range.max ).toLocaleString() }` ) : 'N/A' })</option> ) }
            </select>
            <button type="button" className="btn btn-primary" onClick={ handleAddProduct }>
              <FaPlus /> Add Product
            </button>
          </div>

          { items.length > 0 ? (
            <div className="order-items-builder">
              { items.map( ( item, index ) => (
                <div className="order-item-builder" key={ index }>
                  <div className="item-builder-header">
                    <strong>{ item.product_name }</strong>
                    <div className="qty-row">
                      <button type="button" onClick={ () => handleQuantityChange( index, item.quantity - 1 ) } disabled={ item.quantity <= 1 }>-</button>
                      <span>
                        { ( () => {
                          const pv = getItemPreview( item );
                          if ( pv && pv.bonus_quantity ) {
                            const pct = pv.bogo_info && pv.bogo_info.get_discount_percent != null ? parseFloat( pv.bogo_info.get_discount_percent ) : null;
                            const isFullFree = pct != null && pct >= 100;
                            if ( isFullFree ) {
                              return `${item.quantity} + ${pv.bonus_quantity} FREE`;
                            }
                            return `${item.quantity}`;
                          }
                          return item.quantity;
                        } )() }
                      </span>
                      <button
                        type="button"
                        onClick={ () => handleQuantityChange( index, item.quantity + 1 ) }
                        disabled={ item.stock_quantity !== undefined && item.quantity >= item.stock_quantity }
                      >
                        +
                      </button>
                    </div>
                    <button type="button" className="btn-remove-item" onClick={ () => handleRemoveItem( index ) }>
                      <FaTrash />
                    </button>
                  </div>
                  { item.attributes?.length > 0 && (
                     <div className="item-options">
                       { item.attributes.map( ( attr ) => (
                         <div className="option-group" key={ attr.id }>
                           <span className="option-name">{ attr.name }:</span>
                           <select
                             value={ item.selected_options[ attr.id ] || '' }
                             onChange={ ( e ) => handleOptionChange( index, attr.id, parseInt( e.target.value ) ) }
                           >
                             <option value="">Select...</option>
                             { attr.options.map( ( opt ) => (
                               <option key={ opt.id } value={ opt.id }>
                                 { opt.value }
                               </option>
                             ) ) }
                           </select>
                         </div>
                       ) ) }
                       { Object.keys( item.selected_options || {} ).length > 0 && (
                         <button type="button" className="btn-reset-options" onClick={ () => handleResetOptions( index ) }>
                           Reset
                         </button>
                       ) }
                     </div>
                   ) }
                    { item.stock_quantity !== undefined && item.stock_quantity !== null && (
                      <div className="item-stock-info">
                        { item.stock_quantity > 0
                          ? `Stock: ${ item.stock_quantity } available`
                          : 'Out of stock' }
                      </div>
                    ) }
                    { ( () => {
                      const pv = getItemPreview( item );
                      if ( !pv || !pv.bonus_quantity ) return null;
                      const pct = pv.bogo_info && pv.bogo_info.get_discount_percent != null ? parseFloat( pv.bogo_info.get_discount_percent ) : null;
                      const isFullFree = pct != null && pct >= 100;
                      if ( !isFullFree ) return null;
                      const label = `+ ${pv.bonus_quantity} FREE`;
                      return <div className="admin-bogo-badge"> {label} (BOGO)</div>;
                    } )() }
                    <div className="item-builder-total">
                      { ( () => {
                        const pv = getItemPreview( item );
                        if ( pv && pv.discounted_subtotal ) {
                          return <>৳{ parseFloat( pv.discounted_subtotal ).toLocaleString() }</>;
                        }
                        if ( item.price_at_purchase !== undefined && item.price_at_purchase !== null ) {
                          return <>৳{ parseFloat( item.price_at_purchase ).toLocaleString() }</>;
                        }
                        if ( item.unit_price !== undefined ) {
                          return <>৳{ parseFloat( item.unit_price ).toLocaleString() } × { item.quantity } = ৳{ ( parseFloat( item.unit_price ) * item.quantity ).toLocaleString() }</>;
                        }
                        return <span className="price-placeholder">৳0.00</span>;
                      } )() }
                    </div>
                </div>
              ) ) }
            </div>
          ) : (
            <p className="no-items-hint">No products added yet. Select a product above.</p>
          ) }
        </div>

         {/* Summary & Submit */ }
        <div className="order-detail-card">
          <h3>Order Total</h3>
          { preview && preview.bogo_free_note && (
            <div className="success-discount-row" style={{ marginBottom: '8px' }}>
              <span>{preview.bogo_free_note}</span>
            </div>
          )}
          { preview && preview.discount_breakdown && preview.discount_breakdown.length > 0 && (
            <div className="discount-breakdown-detail">
              <h4>Discount Applied</h4>
              {preview.discount_breakdown.filter((entry) => parseFloat(entry.amount || 0) > 0 || entry.type === 'bogo').map((entry, idx) => {
                const isBogoFree = entry.type === 'bogo' && parseFloat(entry.get_discount_percent || entry['get_discount_percent'] || 0) >= 100;
                return (
                  <div className="discount-summary-row" key={idx}>
                    <span className="discount-label">
                      {entry.name || (entry.type === 'price_discount' ? 'Discount' : entry.type)}
                    </span>
                    <span className="discount-value">
                      {isBogoFree ? 'FREE' : `-৳${parseFloat(entry.amount || 0).toLocaleString()}`}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
          { preview && preview.free_shipping && (
            <div className="discount-summary-row">
              <span className="discount-label">Shipping</span>
              <span className="discount-value">🚚 Free Shipping</span>
            </div>
          )}
          <p className="total-price">৳{ previewTotal.toLocaleString() }</p>
          { previewLoading && <p className="text-muted">Calculating discounts...</p> }
          <button type="submit" className="btn btn-primary btn-lg" disabled={ saving }>
            <FaSave /> { saving ? 'Saving...' : isEditing ? 'Update Order' : 'Create Order' }
          </button>
        </div>
      </form>
    </div>
  );
}

export default AdminOrderCreate;