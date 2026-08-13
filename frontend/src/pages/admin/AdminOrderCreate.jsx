import { useEffect, useState } from 'react';
import { FaArrowLeft, FaPlus, FaSave, FaTrash } from 'react-icons/fa';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { adminCreateOrder, adminGetOrder, adminGetProduct, adminGetProducts, adminUpdateOrder } from '../../api/adminServices';
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

  const resolveItemPrice = async ( item ) => {
    if ( !item.attributes || item.attributes.length === 0 ) return null;
    const selectedOptions = item.selected_options || {};
    const allSelected = item.attributes.every( ( attr ) => selectedOptions[ attr.id ] );
    if ( !allSelected ) return null;

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

    if ( Object.keys( selectedAttrs ).length === 0 ) return null;

    try {
      const data = await findVariant( item.product_id, selectedAttrs );
      const price = data.variant?.price;
      return price || null;
    } catch ( err ) {
      return null;
    }
  };

  const handleOptionChange = async ( index, attrId, optionId ) => {
    const newItems = [ ...items ];
    const selected_options = { ...newItems[ index ].selected_options, [ attrId ]: optionId };
    newItems[ index ] = { ...newItems[ index ], selected_options, unit_price: undefined };
    setItems( newItems );

    const price = await resolveItemPrice( newItems[ index ] );
    if ( price ) {
      setItems( ( prev ) => prev.map( ( it, i ) => ( i === index ? { ...it, unit_price: price } : it ) ) );
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

        // Build items immediately from order data
        const baseItems = ( order.items || [] ).map( ( item ) => {
          let selected_options = {};
          if ( item.selected_attributes ) {
            try { selected_options = JSON.parse( item.selected_attributes ); } catch { }
          }
          return {
            product_id: item.product_id,
            product_name: item.product_name || `Product #${ item.product_id }`,
            quantity: item.quantity,
            selected_options,
            attributes: [],
          };
        } );
        setItems( baseItems );

        // Then asynchronously load product attributes for each item
        for ( const item of baseItems ) {
          try {
            const detail = await loadProductDetail( item.product_id );
            if ( detail?.attributes ) {
              setItems( ( prev ) => prev.map( ( it ) =>
                it.product_id === item.product_id ? { ...it, attributes: detail.attributes } : it
              ) );
              // Resolve variant price for this item
              const price = await resolveItemPrice( { ...item, attributes: detail.attributes } );
              if ( price !== null ) {
                setItems( ( prev ) => prev.map( ( it ) =>
                  it.product_id === item.product_id ? { ...it, unit_price: price } : it
                ) );
              }
            }
          } catch { }
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
    setItems( ( prev ) => [
      ...prev,
      {
        product_id: pid,
        product_name: product.name,
        quantity: 1,
        selected_options: {},
        attributes: detail?.attributes || [],
      },
    ] );
    setSelectedProductId( '' );
  };

  const handleQuantityChange = ( index, qty ) => {
    setItems( ( prev ) => prev.map( ( it, i ) => ( i === index ? { ...it, quantity: Math.max( 1, qty ) } : it ) ) );
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
    let unit;
    if ( item.unit_price !== undefined ) {
      unit = parseFloat( item.unit_price );
    } else {
      unit = 0;
    }
    return unit * item.quantity;
  };

  const totalPrice = items.reduce( ( sum, it ) => sum + calculateItemTotal( it ), 0 );

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
                      <button type="button" onClick={ () => handleQuantityChange( index, item.quantity - 1 ) }>-</button>
                      <span>{ item.quantity }</span>
                      <button type="button" onClick={ () => handleQuantityChange( index, item.quantity + 1 ) }>+</button>
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
                  <div className="item-builder-total">
                    { item.unit_price !== undefined ? (
                      <>৳{ parseFloat( item.unit_price ).toLocaleString() } × { item.quantity } = ৳{ ( parseFloat( item.unit_price ) * item.quantity ).toLocaleString() }</>
                    ) : (
                      <span className="price-placeholder">৳0.00</span>
                    ) }
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
          <p className="total-price">৳{ totalPrice.toLocaleString() }</p>
          <button type="submit" className="btn btn-primary btn-lg" disabled={ saving }>
            <FaSave /> { saving ? 'Saving...' : isEditing ? 'Update Order' : 'Create Order' }
          </button>
        </div>
      </form>
    </div>
  );
}

export default AdminOrderCreate;