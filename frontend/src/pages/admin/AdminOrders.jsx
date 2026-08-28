import { useEffect, useState } from 'react';
import { FaBan, FaEye, FaFileExcel, FaFileCsv, FaFileInvoice, FaPlus, FaSearch, FaTrash } from 'react-icons/fa';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  adminCreateInvoiceTicket,
  adminDeleteOrder,
  adminExportOrders,
  adminGetOrders,
  adminSearchOrders,
  adminUpdateOrderStatus,
} from '../../api/adminServices';
import { API_BASE_URL } from '../../api/client';
import Modal from '../../components/Modal';
import Pagination from '../../components/Pagination';
import { useToast } from '../../context/ToastContext';

const PAGE_SIZE = 20;

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

function getErrorMessage ( err, fallback ) {
  const detail = err?.response?.data?.detail;
  if ( !detail ) return fallback;
  if ( typeof detail === 'string' ) return detail;
  if ( Array.isArray( detail ) ) {
    return detail
      .map( ( d ) => `${ ( d.loc || [] ).slice( 1 ).join( '.' ) }: ${ d.msg }` )
      .join( ', ' );
  }
  return JSON.stringify( detail );
}

function AdminOrders () {
  const navigate = useNavigate();
  const location = useLocation();
  const { addToast } = useToast();
  const [ orders, setOrders ] = useState( [] );
  const [ total, setTotal ] = useState( 0 );
  const [ page, setPage ] = useState( 0 );
  const [ loading, setLoading ] = useState( true );
  const [ invoiceLoadingId, setInvoiceLoadingId ] = useState( null );
  const [ statusFilter, setStatusFilter ] = useState( '' );
  const [ periodFilter, setPeriodFilter ] = useState( 'all' );
  const [ filterYear, setFilterYear ] = useState( new Date().getFullYear() );
  const [ filterMonth, setFilterMonth ] = useState( new Date().getMonth() + 1 );
  const [ filterDate, setFilterDate ] = useState( new Date().toISOString().slice( 0, 10 ) );
  const [ searchType, setSearchType ] = useState( 'all' );
  const [ searchValue, setSearchValue ] = useState( '' );
  const [ activeSearch, setActiveSearch ] = useState( { type: 'phone', value: '' } );
  const [ deleteModal, setDeleteModal ] = useState( { show: false, id: null, number: '' } );
  const [ cancelModal, setCancelModal ] = useState( { show: false, id: null, number: '' } );

  const loadOrders = async ( status = statusFilter, pageNum = page, searchObj = activeSearch, period = periodFilter, yr = filterYear, mo = filterMonth, dt = filterDate ) => {
    try {
      setLoading( true );
      if ( searchObj.value.trim() ) {
        const data = await adminSearchOrders( searchObj.type, searchObj.value.trim(), {
          skip: pageNum * PAGE_SIZE,
          limit: PAGE_SIZE,
        } );
        setOrders( data.orders || [] );
        setTotal( data.total || 0 );
      } else {
        const params = {
          skip: pageNum * PAGE_SIZE,
          limit: PAGE_SIZE,
        };
        if ( status ) params.status = status;
        if ( period !== 'all' ) {
          params.period = period;
          if ( period === 'year' ) params.year = yr;
          if ( period === 'month' ) { params.year = yr; params.month = mo; }
          if ( period === 'day' ) params.date = dt;
        }
        const data = await adminGetOrders( params );
        setOrders( data.orders || [] );
        setTotal( data.total || 0 );
      }
    } catch ( err ) {
      addToast( getErrorMessage( err, 'Failed to load orders.' ), 'error' );
    } finally {
      setLoading( false );
    }
  };

  useEffect( () => {
    const params = new URLSearchParams( location.search );
    const initialStatus = params.get( 'status' ) || '';
    setStatusFilter( initialStatus );
    loadOrders( initialStatus, 0, { type: 'all', value: '' } );
  }, [] );

  const handleStatusChange = ( e ) => {
    const value = e.target.value;
    setStatusFilter( value );
    setPage( 0 );
    navigate( { pathname: '/admin/orders', search: value ? `?status=${ value }` : '' }, { replace: true } );
    loadOrders( value, 0, activeSearch );
  };

  const handlePeriodChange = ( e ) => {
    const value = e.target.value;
    setPeriodFilter( value );
    setPage( 0 );
    loadOrders( statusFilter, 0, activeSearch, value, filterYear, filterMonth );
  };

  const handleFilterYearChange = ( e ) => {
    const value = parseInt( e.target.value );
    setFilterYear( value );
    setPage( 0 );
    loadOrders( statusFilter, 0, activeSearch, periodFilter, value, filterMonth );
  };

  const handleFilterMonthChange = ( e ) => {
    const value = parseInt( e.target.value );
    setFilterMonth( value );
    setPage( 0 );
    loadOrders( statusFilter, 0, activeSearch, periodFilter, filterYear, value );
  };

  const handleFilterDateChange = ( e ) => {
    const value = e.target.value;
    setFilterDate( value );
    setPage( 0 );
    loadOrders( statusFilter, 0, activeSearch, periodFilter, filterYear, filterMonth, value );
  };

  const handlePageChange = ( newPage ) => {
    setPage( newPage );
    loadOrders( statusFilter, newPage, activeSearch );
  };

  const handleStatusUpdate = async ( orderId, newStatus ) => {
    try {
      await adminUpdateOrderStatus( orderId, newStatus );
      await loadOrders( statusFilter, page, activeSearch );
      addToast( 'Order status updated!', 'success' );
      window.dispatchEvent( new CustomEvent( 'order-status-updated' ) );
    } catch ( err ) {
      addToast( getErrorMessage( err, 'Failed to update order status.' ), 'error' );
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
      await loadOrders( statusFilter, page, activeSearch );
      addToast( 'Order cancelled successfully!', 'success' );
      window.dispatchEvent( new CustomEvent( 'order-status-updated' ) );
    } catch ( err ) {
      addToast( getErrorMessage( err, 'Failed to cancel order.' ), 'error' );
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
      setPage( 0 );
      await loadOrders( statusFilter, 0, activeSearch );
      addToast( 'Order deleted successfully!', 'success' );
      window.dispatchEvent( new CustomEvent( 'order-status-updated' ) );
    } catch ( err ) {
      addToast( getErrorMessage( err, 'Failed to delete order.' ), 'error' );
    }
  };

  const buildExportParams = () => {
    const params = {};
    if ( statusFilter ) params.status = statusFilter;
    if ( periodFilter !== 'all' ) {
      params.period = periodFilter;
      if ( periodFilter === 'year' ) params.year = filterYear;
      if ( periodFilter === 'month' ) { params.year = filterYear; params.month = filterMonth; }
      if ( periodFilter === 'day' ) params.date = filterDate;
    }
    if ( activeSearch.value.trim() ) {
      params.search_type = activeSearch.type || 'all';
      params.search_value = activeSearch.value.trim();
    }
    return params;
  };

  const handleExport = async ( suffix ) => {
    try {
      const filename = await adminExportOrders( buildExportParams(), suffix );
      addToast( `${ filename } downloaded!`, 'success' );
    } catch ( err ) {
      addToast( getErrorMessage( err, 'Failed to export orders.' ), 'error' );
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
      addToast( getErrorMessage( err, 'Failed to generate invoice.' ), 'error' );
    } finally {
      setInvoiceLoadingId( null );
    }
  };

  const handleSearch = async ( e ) => {
    e.preventDefault();
    const searchObj = { type: searchType, value: searchValue.trim() };
    setActiveSearch( searchObj );
    setPage( 0 );
    loadOrders( statusFilter, 0, searchObj );
  };

  const handleClearSearch = () => {
    setSearchValue( '' );
    const searchObj = { type: searchType, value: '' };
    setActiveSearch( searchObj );
    setPage( 0 );
    loadOrders( statusFilter, 0, searchObj );
  };

  const availableYears = [];
  const currentYear = new Date().getFullYear();
  for ( let y = currentYear - 5; y <= currentYear; y++ ) availableYears.push( y );
  const months = Array.from( { length: 12 }, ( _, i ) => i + 1 );

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h2>Orders</h2>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={ () => handleExport( 'xlsx' ) } title="Export orders to Excel">
            <FaFileExcel /> Excel
          </button>
          <button className="btn btn-secondary" onClick={ () => handleExport( 'csv' ) } title="Export orders to CSV">
            <FaFileCsv /> CSV
          </button>
          <button className="btn btn-primary" onClick={ () => navigate( '/admin/orders/new' ) }>
            <FaPlus /> Create Order
          </button>
        </div>
      </div>

      {/* Filters */ }
      <div className="admin-filters">
        <div className="admin-filters-group">
        <select value={ statusFilter } onChange={ handleStatusChange }>
          <option value="">All Statuses</option>
          { Object.entries( STATUS_LABELS ).map( ( [ value, label ] ) => (
            <option key={ value } value={ value }>{ label }</option>
          ) ) }
        </select>

        <select value={ periodFilter } onChange={ handlePeriodChange }>
          <option value="all">All Time</option>
          <option value="year">Year</option>
          <option value="month">Month</option>
          <option value="day">Date</option>
        </select>
        { periodFilter === 'year' && (
          <select value={ filterYear } onChange={ handleFilterYearChange }>
            { availableYears.map( ( y ) => <option key={ y } value={ y }>{ y }</option> ) }
          </select>
        ) }
        { periodFilter === 'month' && (
          <>
            <select value={ filterYear } onChange={ handleFilterYearChange }>
              { availableYears.map( ( y ) => <option key={ y } value={ y }>{ y }</option> ) }
            </select>
            <select value={ filterMonth } onChange={ handleFilterMonthChange }>
              { months.map( ( m ) => (
                <option key={ m } value={ m }>
                  { new Date( 2000, m - 1, 1 ).toLocaleString( 'default', { month: 'long' } ) }
                </option>
              ) ) }
            </select>
          </>
        ) }
        { periodFilter === 'day' && (
          <input
            type="date"
            value={ filterDate }
            max={ new Date().toISOString().slice( 0, 10 ) }
            onChange={ handleFilterDateChange }
          />
        ) }
        </div>

        <form className="admin-search" onSubmit={ handleSearch }>
          <select value={ searchType } onChange={ ( e ) => setSearchType( e.target.value ) }>
            <option value="all">All</option>
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
          { activeSearch.value && (
            <button type="button" className="btn btn-secondary btn-sm" onClick={ handleClearSearch }>
              Clear
            </button>
          ) }
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

      {/* Pagination */}
      { !loading && (
        <Pagination
          page={ page }
          total={ total }
          pageSize={ PAGE_SIZE }
          onPageChange={ handlePageChange }
          loading={ loading }
        />
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