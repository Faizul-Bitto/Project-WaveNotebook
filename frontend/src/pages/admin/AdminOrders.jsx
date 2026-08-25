import { useEffect, useState } from 'react';
import { FaBan, FaEye, FaFileInvoice, FaPlus, FaSearch, FaTrash } from 'react-icons/fa';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  adminCreateInvoiceTicket,
  adminDeleteOrder,
  adminGetOrders,
  adminSearchOrders,
  adminUpdateOrderStatus,
} from '../../api/adminServices';
import { API_BASE_URL } from '../../api/client';
import Modal from '../../components/Modal';
import { useToast } from '../../context/ToastContext';

const STATUS_LABELS = {
  pending: 'Pending',
  called: 'Called',
  confirmed: 'Confirmed',
  processing: 'Processing',
  shipped: 'Shipped',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
  returned: 'Returned',
};

const STATUS_DROPDOWN_LABELS = {
  pending: 'Pending',
  called: 'Called',
  confirmed: 'Confirmed',
  processing: 'Processing',
  shipped: 'Shipped',
  delivered: 'Delivered',
  returned: 'Returned',
  cancelled: 'Cancelled',
};

function AdminOrders () {
  const navigate = useNavigate();
  const location = useLocation();
  const { addToast } = useToast();
  const [ orders, setOrders ] = useState( [] );
  const [ loading, setLoading ] = useState( true );
  const [ invoiceLoadingId, setInvoiceLoadingId ] = useState( null );
  const [ statusFilter, setStatusFilter ] = useState( '' );
  const [ searchType, setSearchType ] = useState( 'phone' );
  const [ searchValue, setSearchValue ] = useState( '' );
  const [ deleteModal, setDeleteModal ] = useState( { show: false, id: null, number: '' } );
  const [ cancelModal, setCancelModal ] = useState( { show: false, id: null, number: '' } );

  const loadOrders = async ( status = '' ) => {
    try {
      setLoading( true );
      const params = {};
      if ( status ) params.status = status;
      const data = await adminGetOrders( params );
      setOrders( data.orders || [] );
    } catch ( err ) {
      addToast( err.response?.data?.detail || 'Failed to load orders.', 'error' );
    } finally {
      setLoading( false );
    }
  };

  useEffect( () => {
    const params = new URLSearchParams( location.search );
    const initialStatus = params.get( 'status' ) || '';
    setStatusFilter( initialStatus );
    loadOrders( initialStatus );
  }, [] );

  const handleStatusChange = ( e ) => {
    const value = e.target.value;
    setStatusFilter( value );
    navigate( { pathname: '/admin/orders', search: value ? `?status=${ value }` : '' }, { replace: true } );
    loadOrders( value );
  };

  const handleStatusUpdate = async ( orderId, newStatus ) => {
    try {
      await adminUpdateOrderStatus( orderId, newStatus );
      await loadOrders( statusFilter );
      addToast( 'Order status updated!', 'success' );
      window.dispatchEvent( new CustomEvent( 'order-status-updated' ) );
    } catch ( err ) {
      addToast( err.response?.data?.detail || 'Failed to update order status.', 'error' );
    }
  };

  const handleCancelOrder = ( orderId, orderNumber ) => {
    setCancelModal( { show: true, id: orderId, number: orderNumber } );
  };

  const confirmCancel = async () => {
    const { id } = cancelModal;
    setCancelModal( { show: false, id: null, number: '' } );
    try {
      await adminUpdateOrderStatus( id, 'cancelled' );
      await loadOrders( statusFilter );
      addToast( 'Order cancelled successfully!', 'success' );
      window.dispatchEvent( new CustomEvent( 'order-status-updated' ) );
    } catch ( err ) {
      addToast( err.response?.data?.detail || 'Failed to cancel order.', 'error' );
    }
  };

  const handleDelete = async ( orderId, orderNumber ) => {
    setDeleteModal( { show: true, id: orderId, number: orderNumber } );
  };

  const confirmDelete = async () => {
    const { id } = deleteModal;
    setDeleteModal( { show: false, id: null, number: '' } );
    try {
      await adminDeleteOrder( id );
      await loadOrders( statusFilter );
      addToast( 'Order deleted successfully!', 'success' );
      window.dispatchEvent( new CustomEvent( 'order-status-updated' ) );
    } catch ( err ) {
      addToast( err.response?.data?.detail || 'Failed to delete order.', 'error' );
    }
  };

  const handleDownloadInvoice = async ( orderId ) => {
    setInvoiceLoadingId( orderId );
    try {
      const { ticket } = await adminCreateInvoiceTicket( orderId );
      const url = `${API_BASE_URL}/admin/orders/${orderId}/invoice?ticket=${ticket}`;
      const link = document.createElement( 'a' );
      link.href = url;
      link.rel = 'noopener';
      document.body.appendChild( link );
      link.click();
      link.remove();
      addToast( 'Invoice generated! Download starting...', 'success' );
    } catch ( err ) {
      addToast( err.response?.data?.detail || 'Failed to generate invoice.', 'error' );
    } finally {
      setInvoiceLoadingId( null );
    }
  };

  const handleSearch = async ( e ) => {
    e.preventDefault();
    if ( !searchValue.trim() ) {
      loadOrders( statusFilter );
      return;
    }
    try {
      setLoading( true );
      const data = await adminSearchOrders( searchType, searchValue.trim() );
      setOrders( data.orders || [] );
    } catch ( err ) {
      addToast( err.response?.data?.detail || 'Failed to search orders.', 'error' );
    } finally {
      setLoading( false );
    }
  };

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h2>Orders</h2>
        <div className="header-actions">
          <button className="btn btn-primary" onClick={ () => navigate( '/admin/orders/new' ) }>
            <FaPlus /> Create Order
          </button>
        </div>
      </div>

      {/* Filters */ }
      <div className="admin-filters">
        <select value={ statusFilter } onChange={ handleStatusChange }>
          <option value="">All Statuses</option>
          { Object.entries( STATUS_LABELS ).map( ( [ value, label ] ) => (
            <option key={ value } value={ value }>{ label }</option>
          ) ) }
        </select>

        <form className="admin-search" onSubmit={ handleSearch }>
          <select value={ searchType } onChange={ ( e ) => setSearchType( e.target.value ) }>
            <option value="phone">Phone</option>
            <option value="name">Name</option>
            <option value="address">Address</option>
            <option value="order_number">Order Number</option>
          </select>
          <input
            type="text"
            placeholder="Search..."
            value={ searchValue }
            onChange={ ( e ) => setSearchValue( e.target.value ) }
          />
          <button type="submit" className="btn btn-primary">
            <FaSearch />
          </button>
        </form>
      </div>

      { loading ? (
        <div className="loading">Loading orders...</div>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Order #</th>
                <th>Customer</th>
                <th>Phone</th>
                <th>District</th>
                <th>Subtotal</th>
                <th>Discount</th>
                <th>Total</th>
                <th>Status</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              { orders.length === 0 ? (
                <tr>
                  <td colSpan="10" className="table-empty">No orders found</td>
                </tr>
              ) : (
                orders.map( ( order ) => (
                  <tr key={ order.id }>
                    <td>{ order.order_number }</td>
                    <td>{ order.full_name }</td>
                    <td>{ order.phone_number }</td>
                    <td>{ order.district }</td>
                    <td>৳{ ( parseFloat( order.total_price ) + ( parseFloat( order.total_discount ) || 0 ) ).toLocaleString() }</td>
                    <td>
                      { parseFloat( order.total_discount ) > 0 ? (
                        <span className="discount-amount">-৳{ parseFloat( order.total_discount ).toLocaleString() }</span>
                      ) : (
                        <span className="text-muted">-</span>
                      ) }
                    </td>
                    <td className="total-price">৳{ parseFloat( order.total_price ).toLocaleString() }</td>
                    <td>
                      { order.status === 'cancelled' || order.status === 'returned' ? (
                        <span className={ `status-badge status-${ order.status }` }>
                          { STATUS_LABELS[ order.status ] || order.status }
                        </span>
                      ) : (
                        <select
                          className={ `status-select status-${ order.status }` }
                          value={ order.status }
                          onChange={ ( e ) => handleStatusUpdate( order.id, e.target.value ) }
                        >
                          { Object.entries( STATUS_DROPDOWN_LABELS ).map( ( [ value, label ] ) => (
                            <option key={ value } value={ value }>{ label }</option>
                          ) ) }
                        </select>
                      ) }
                    </td>
                    <td>{ new Date( order.created_at ).toLocaleDateString() }</td>
                    <td>
                       <div className="table-actions">
                         <button
                           className="action-btn action-invoice"
                           onClick={ () => handleDownloadInvoice( order.id ) }
                           aria-label={ `Download invoice for order ${ order.order_number }` }
                           disabled={ invoiceLoadingId === order.id }
                         >
                           <FaFileInvoice />
                         </button>
                         <button
                           className="action-btn action-edit"
                           onClick={ () => navigate( `/admin/orders/${ order.id }` ) }
                           aria-label={ `View order ${ order.order_number }` }
                         >
                           <FaEye />
                         </button>
                         <button
                           className="action-btn action-delete"
                           onClick={ () => handleDelete( order.id, order.order_number ) }
                           aria-label={ `Delete order ${ order.order_number }` }
                         >
                           <FaTrash />
                         </button>
                        { order.status !== 'cancelled' && order.status !== 'returned' && (
                          <button
                            className="action-btn action-cancel"
                            onClick={ () => handleCancelOrder( order.id, order.order_number ) }
                            aria-label={ `Cancel order ${ order.order_number }` }
                          >
                            <FaBan />
                          </button>
                        ) }
                      </div>
                    </td>
                  </tr>
                ) )
              ) }
            </tbody>
          </table>
        </div>
      ) }

      <Modal
        isOpen={ deleteModal.show }
        onClose={ () => setDeleteModal( { show: false, id: null, number: '' } ) }
        onConfirm={ confirmDelete }
        title="Delete Order"
        message={ `Are you sure you want to delete order ${ deleteModal.number }?` }
        confirmText="Delete"
        type="danger"
      />

      <Modal
        isOpen={ cancelModal.show }
        onClose={ () => setCancelModal( { show: false, id: null, number: '' } ) }
        onConfirm={ confirmCancel }
        title="Cancel Order"
        message={ `Are you sure you want to cancel order ${ cancelModal.number }?` }
        confirmText="Cancel Order"
        type="danger"
      />
    </div>
  );
}

export default AdminOrders;