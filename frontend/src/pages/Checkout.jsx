import { useEffect, useState } from 'react';
import { FaCheckCircle, FaCopy, FaTruck } from 'react-icons/fa';
import { Link } from 'react-router-dom';
import { createOrder, getDistricts } from '../api/services';
import PhoneInput from '../components/PhoneInput';
import { useCart } from '../context/CartContext';
import { useDirectBuy } from '../context/DirectBuyContext';
import { useToast } from '../context/ToastContext';

// Build a BOGO label for an item that has free/discounted bonus units.
// For 100% free BOGO: bonus items are added on top (show "+ N FREE").
// For partial (<100%) BOGO: discounted items are within the purchased
// quantity — no extra badge shown; the discount appears in the summary.
function getBogoInfo ( item ) {
  const bonus = item.bonus_quantity || item.bogo_bonus_quantity || 0;
  if ( !bonus ) return null;
  const pct = item.bogo_get_discount_percent;
  const isFullFree = pct != null && pct >= 100;
  if ( !isFullFree ) return null;
  const label = `${ bonus } FREE`;
  return { bonus, label, isFullFree };
}

function Checkout () {
  const { cart, clearAll, totalDiscount, totalAfterDiscount, discountBreakdown, freeShipping, simpleBogo, bogoFreeNote, getShippingChargeForDistrict, shippingCharges } = useCart();
  const { directItem } = useDirectBuy();
  const { addToast } = useToast();
  const [ districts, setDistricts ] = useState( [] );
  const [ loading, setLoading ] = useState( false );
  const [ orderSuccess, setOrderSuccess ] = useState( null );
  const [ formData, setFormData ] = useState( {
    full_name: '',
    phone_number: '',
    email: '',
    district: '',
    thana: '',
    note: '',
    address: '',
  } );

  const shippingCharge = !freeShipping ? getShippingChargeForDistrict( formData.district ) : null;

  useEffect( () => {
    const loadDistricts = async () => {
      try {
        const data = await getDistricts();
        setDistricts( data.districts || [] );
      } catch ( err ) {
        console.error( 'Failed to load districts:', err );
      }
    };
    loadDistricts();
  }, [] );

  const handleChange = ( e ) => {
    setFormData( {
      ...formData,
      [ e.target.name ]: e.target.value,
    } );
  };

  const handleSubmit = async ( e ) => {
    e.preventDefault();

    // Validate
    if ( !formData.full_name.trim() ) {
      addToast( 'Please enter your full name.', 'error' );
      return;
    }
    if ( !formData.phone_number.trim() || formData.phone_number.trim().length < 11 ) {
      addToast( 'Please enter a valid phone number (11 digits).', 'error' );
      return;
    }
    if ( !formData.district ) {
      addToast( 'Please select your district.', 'error' );
      return;
    }
    if ( !formData.thana.trim() ) {
      addToast( 'Please enter your thana / upazila.', 'error' );
      return;
    }
    if ( !formData.address.trim() ) {
      addToast( 'Please enter your address.', 'error' );
      return;
    }

    let items;
    if ( directItem ) {
      items = [ { product_id: directItem.product.id, quantity: directItem.quantity, selected_attributes: directItem.attrsString } ];
    } else {
      items = ( cart?.items || [] ).map( ( item ) => ( {
        product_id: item.product_id,
        quantity: item.quantity,
        selected_attributes: item.selected_attributes || null,
      } ) );
    }

    if ( items.length === 0 ) {
      addToast( directItem ? 'Product not available.' : 'Your cart is empty.', 'error' );
      return;
    }

    try {
      setLoading( true );
      const orderData = {
        full_name: formData.full_name,
        phone_number: formData.phone_number,
        email: formData.email || null,
        district: formData.district,
        thana: formData.thana,
        note: formData.note || null,
        address: formData.address,
        items,
      };
      const result = await createOrder( orderData );
      setOrderSuccess( result.order );
      await clearAll();
      addToast( 'Order placed successfully!', 'success' );
    } catch ( err ) {
      addToast( err.response?.data?.detail || 'Failed to place order. Please try again.', 'error' );
    } finally {
      setLoading( false );
    }
  };

  // Compute effective unit price for a direct item (selected variant price)
  const computeDirectUnitPrice = () => {
    if ( !directItem ) return 0;
    let price = directItem.variant?.price
      ? parseFloat( directItem.variant.price )
      : ( directItem.product.price_range ? parseFloat( directItem.product.price_range.min ) : 0 );
    return price;
  };

  const directUnitPrice = computeDirectUnitPrice();
  const items = directItem ? [ {
    id: 'direct',
    product_name: directItem.product.name,
    slug: directItem.product.slug,
    quantity: directItem.quantity,
    unit_price: directUnitPrice,
    selected_attributes_display: directItem.product.attributes
      ?.filter( ( attr ) => directItem.selectedOptions?.[ attr.id ] )
      .map( ( attr ) => {
        const opt = ( attr.options || [] ).find( ( o ) => o.id === directItem.selectedOptions[ attr.id ] );
        return `${ attr.name }: ${ opt ? opt.value : '' }`;
      } )
      .join( ', ' ) || undefined,
    subtotal: ( directUnitPrice * directItem.quantity ).toFixed( 2 ),
  } ] : ( cart?.items || [] );
  const totalPrice = directItem
    ? directUnitPrice * directItem.quantity
    : parseFloat( cart?.total_price || '0' );

  // Order success screen - use API response data (items, total) not cart state
  if ( orderSuccess ) {
    const successItems = orderSuccess.items || [];
    const successTotal = orderSuccess.total_price
      ? parseFloat( orderSuccess.total_price )
      : 0;
    const successSimpleBogo = orderSuccess.simple_bogo === true;
    const successBogoFreeNote = orderSuccess.bogo_free_note || null;

    return (
      <div className="container order-success">
        <FaCheckCircle className="success-icon" />
        <h1>Order Placed Successfully!</h1>

        {/* Highlighted message for the customer */ }
        <div className="order-notice-box">
          <p className="order-notice-text">
            <strong>Dear Customer,</strong>
          </p>
          <p className="order-notice-text">
            Thank you for placing your order with us!
          </p>
          <p className="order-notice-text">
            Your order has been received successfully. One of our representatives will contact you shortly via <strong>phone call or WhatsApp</strong> to confirm your order.
          </p>
          <p className="order-notice-text">
            We truly appreciate your trust and look forward to serving you.
          </p>
        </div>

        <div className="order-number-highlight">
          <p className="order-number">
            Order Number: <strong>{ orderSuccess.order_number }</strong>
            <button
              type="button"
              className="btn btn-copy"
              onClick={ () => {
                navigator.clipboard.writeText( orderSuccess.order_number );
                addToast( 'Order number copied!', 'success' );
              } }
              title="Copy order number for tracking"
            >
              <FaCopy /> Copy
            </button>
          </p>
          <p className="order-number-hint">
            Copy the order number above to track your order status.
          </p>
        </div>

        <div className="order-summary-box">
          <h3>Order Summary</h3>
          <p><strong>Name:</strong> { orderSuccess.full_name }</p>
          <p><strong>Phone:</strong> { orderSuccess.phone_number }</p>
          { orderSuccess.email && <p><strong>Email:</strong> { orderSuccess.email }</p> }
          <p><strong>District:</strong> { orderSuccess.district }</p>
          <p><strong>Thana:</strong> { orderSuccess.thana }</p>
          <p><strong>Address:</strong> { orderSuccess.address }</p>

          { orderSuccess.discount_breakdown && orderSuccess.discount_breakdown.length > 0 && orderSuccess.discount_breakdown
            .filter( ( entry ) => parseFloat( entry.amount || 0 ) > 0 || entry.type === 'bogo' )
            .map( ( entry, idx ) => {
              const isBogoFree = entry.type === 'bogo' && parseFloat(entry.get_discount_percent || entry['get_discount_percent'] || 0) >= 100;
              return (
                <div className="success-discount-row" key={ idx }>
                  <span>
                    { entry.name || ( entry.type === 'price_discount' ? 'Discount' : entry.type ) }
                  </span>
                  <span className="discount-amount">
                    {isBogoFree ? 'FREE' : `-৳${parseFloat(entry.amount || 0).toLocaleString()}`}
                  </span>
                </div>
              );
            } ) }

          { orderSuccess.free_shipping && (
            <div className="success-discount-row">
              <span><span className="fs-badge">🚚</span> Free Shipping</span>
              <span className="free-shipping-text">FREE</span>
            </div>
          ) }

          { successSimpleBogo !== true && orderSuccess.total_discount && parseFloat( orderSuccess.total_discount ) > 0 && (
            <p>
              <strong>Total Discount:</strong>{ ' ' }
              <span className="discount-amount">-৳{ parseFloat( orderSuccess.total_discount ).toLocaleString() }</span>
            </p>
          ) }

          { successBogoFreeNote && (
            <p className="success-bogo-note">
              <strong>
                { successBogoFreeNote }
                { ' ' }— so you got total{ ' ' }
                { successItems.reduce( ( sum, it ) => {
                  const bonus = it.bonus_quantity || it.bogo_bonus_quantity || 0;
                  const pct = it.bogo_get_discount_percent;
                  const isFullFree = bonus > 0 && ( pct == null || pct >= 100 );
                  return sum + ( it.quantity || 0 ) + ( isFullFree ? bonus : 0 );
                }, 0 ) }{ ' ' }
                items in ৳{ successTotal.toLocaleString() }
              </strong>
            </p>
          ) }

          <p><strong>Total:</strong> ৳{ successTotal.toLocaleString() }</p>
          <p><strong>Payment:</strong> Cash on Delivery</p>

          { successItems.length > 0 && (
            <div className="order-success-items">
              <h4 style={ { marginTop: '16px', marginBottom: '8px', fontWeight: 600, color: 'var(--gray-700)' } }>Ordered Items:</h4>
              <ul style={ { listStyle: 'none', padding: 0, margin: 0 } }>
                { successItems.map( ( item, idx ) => {
                  const itemSubtotal = item.price_at_purchase !== undefined
                    ? parseFloat( item.price_at_purchase )
                    : ( parseFloat( item.unit_price || 0 ) * item.quantity );
                  const bonusQty = item.bonus_quantity || item.bogo_bonus_quantity || 0;
                  const bogoPct = item.bogo_get_discount_percent;
                  const isFullFreeBogo = bonusQty > 0 && ( bogoPct == null || bogoPct >= 100 );
                  return (
                    <li
                      key={ item.id || idx }
                      style={ { display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--gray-100)', fontSize: '14px' } }
                    >
                      <span>
                        { item.product_name || `Product #${ item.product_id || '(deleted)' }` }
                        { item.product_code && (
                          <span style={ { display: 'block', fontSize: '12px', color: 'var(--gray-500)' } }>
                            Code: { item.product_code }
                          </span>
                        ) }
                        { item.selected_attributes_display && (
                          <span style={ { display: 'block', fontSize: '12px', color: 'var(--gray-600)' } }>
                            { item.selected_attributes_display }
                          </span>
                        ) }
                        <span style={ { display: 'block', fontSize: '12px', color: 'var(--gray-600)' } }>
                           Qty: { item.quantity }
                           { isFullFreeBogo && (
                             <span style={ { color: 'var(--primary)', fontWeight: 600 } }>
                               { ' ' }+ { bonusQty } FREE
                             </span>
                           ) }
                          { ' ' }× ৳{ parseFloat( item.unit_price || 0 ).toLocaleString() }
                        </span>
                      </span>
                      <span>৳{ itemSubtotal.toLocaleString() }</span>
                    </li>
                  );
                } ) }
              </ul>
            </div>
          ) }

          { !orderSuccess.free_shipping && (
            <div className="checkout-shipment">
              <h3>Shipment</h3>
              <div className="shipment-zones">
                { shippingCharges.map( ( charge ) => (
                  <div className="shipment-zone-row" key={ charge.id }>
                    <span>{ charge.zone_name }</span>
                    <span>৳{ charge.amount }</span>
                  </div>
                ) ) }
              </div>
              <div className="shipment-delivery-time">
                Delivers in: 3-7 Working Days
              </div>
            </div>
          ) }
        </div>
        <Link
          to="/"
          className="btn btn-primary"
        >
          Continue Shopping
        </Link>
      </div>
    );
  }

  if ( items.length === 0 ) {
    return (
      <div className="container empty-state">
        <h2>Your cart is empty</h2>
        <p>Add some products before checking out.</p>
        <Link to="/products" className="btn btn-primary">Browse Products</Link>
      </div>
    );
  }

  return (
    <div className="checkout-page">
      <div className="container">
        <div className="page-header">
          <h1>Checkout</h1>
        </div>

        <div className="checkout-layout">
          {/* Shipping Form */ }
          <form className="checkout-form" onSubmit={ handleSubmit }>
            <h2>Shipping Information</h2>

            <div className="form-group">
              <label htmlFor="full_name">Full Name *</label>
              <input
                type="text"
                id="full_name"
                name="full_name"
                value={ formData.full_name }
                onChange={ handleChange }
                placeholder="Enter your full name"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="phone_number">Phone Number *</label>
              <PhoneInput
                name="phone_number"
                value={ formData.phone_number }
                onChange={ ( name, val ) => setFormData( ( prev ) => ( { ...prev, [ name ]: val } ) ) }
                placeholder="XXXXXXXXXXX"
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email (optional)</label>
              <input
                type="email"
                id="email"
                name="email"
                value={ formData.email }
                onChange={ handleChange }
                placeholder="you@example.com"
              />
            </div>

            <div className="form-group">
              <label htmlFor="district">District *</label>
              <select
                id="district"
                name="district"
                value={ formData.district }
                onChange={ handleChange }
                required
              >
                <option value="">Select District</option>
                { districts.map( ( district ) => (
                  <option key={ district } value={ district }>
                    { district }
                  </option>
                ) ) }
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="thana">Thana *</label>
              <input
                type="text"
                id="thana"
                name="thana"
                value={ formData.thana }
                onChange={ handleChange }
                placeholder="Enter your thana"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="address">Full Address *</label>
              <textarea
                id="address"
                name="address"
                value={ formData.address }
                onChange={ handleChange }
                placeholder="House, Road, Area"
                rows="3"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="note">Note (optional)</label>
              <textarea
                id="note"
                name="note"
                value={ formData.note }
                onChange={ handleChange }
                placeholder="Add a short note for the seller (optional)"
                rows="2"
              />
            </div>

            <div className="payment-method">
              <FaTruck className="payment-icon" />
              <div>
                <h4>Cash on Delivery</h4>
                <p>Pay in cash when you receive your order.</p>
              </div>
            </div>

            <button type="submit" className="btn btn-primary btn-lg" disabled={ loading }>
              { loading ? 'Placing Order...' : 'Place Order' }
            </button>
          </form>

          <div className="checkout-sidebar">
            {/* Order Summary */ }
            <div className="checkout-summary">
              <h2>Order Summary</h2>
              { items.map( ( item ) => (
                <div className="checkout-item" key={ item.id }>
                  <div className="checkout-item-info">
                    <span className="checkout-item-name">{ item.product_name }</span>
                    { item.selected_attributes_display && (
                      <span className="checkout-item-qty">{ item.selected_attributes_display }</span>
                    ) }
                    <span className="checkout-item-qty">
                      Qty: { item.quantity }
                      { getBogoInfo( item ) && (
                        <span className="checkout-bogo-badge"> + { getBogoInfo( item ).label } (BOGO)</span>
                      ) }
                    </span>
                  </div>
                  <span className="checkout-item-price">
                    ৳{ parseFloat( item.discounted_subtotal || item.subtotal ).toLocaleString() }
                  </span>
                </div>
              ) ) }

              { simpleBogo && bogoFreeNote && (
                <div className="checkout-summary-row checkout-bogo-note">
                  <span>{ bogoFreeNote }</span>
                </div>
              ) }

              { !simpleBogo && totalDiscount > 0 && discountBreakdown && discountBreakdown.length > 0 && discountBreakdown
                .filter( ( entry ) => parseFloat( entry.amount || 0 ) > 0 )
                .map( ( entry, idx ) => (
                  <div className="checkout-summary-row checkout-discount-row" key={ idx }>
                    <span>
                      { entry.name || ( entry.type === 'price_discount' ? 'Discount' : entry.type ) }
                    </span>
                    <span className="discount-amount">
                      -৳{ parseFloat( entry.amount || 0 ).toLocaleString() }
                    </span>
                  </div>
                ) ) }

              { freeShipping && (
                <div className="checkout-summary-row checkout-free-shipping">
                  <span><span className="fs-badge">🚚</span> Free Shipping</span>
                  <span className="free-shipping-text">FREE</span>
                </div>
              ) }

              { !simpleBogo && totalDiscount > 0 && (
                <div className="checkout-summary-row checkout-total-discount">
                  <span>Total Discount</span>
                  <span className="discount-amount">-৳{ totalDiscount.toLocaleString() }</span>
                </div>
              ) }

              <div className="checkout-total">
                <span>Total</span>
                <span>৳{ totalAfterDiscount.toLocaleString() }</span>
              </div>
            </div>

            { !freeShipping && (
              <div className="checkout-shipment">
                <h2>Shipment</h2>
                <div className="shipment-zones">
                  { shippingCharges.map( ( charge ) => (
                    <div className="shipment-zone-row" key={ charge.id }>
                      <span>{ charge.zone_name }</span>
                      <span>৳{ charge.amount }</span>
                    </div>
                  ) ) }
                </div>
                <div className="shipment-delivery-time">
                  Delivers in: 3-7 Working Days
                </div>
              </div>
            ) }
          </div>
        </div>
      </div>
    </div> );
}

export default Checkout;
