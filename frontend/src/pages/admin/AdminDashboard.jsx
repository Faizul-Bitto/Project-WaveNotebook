import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FaBox,
  FaShoppingBag,
  FaUsers,
  FaTags,
  FaMoneyBillWave,
  FaPhoneAlt,
  FaCheckCircle,
  FaMoneyCheck,
  FaClock,
  FaCogs,
  FaTruck,
  FaBoxOpen,
  FaBan,
  FaUndo,
} from 'react-icons/fa';
import {
  adminGetProducts,
  adminGetOrders,
  adminGetUsers,
  adminGetCategories,
  adminGetOrderStatusCounts,
  adminGetExpenseSummary,
} from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';

function AdminDashboard() {
  const { addToast } = useToast();
  const [stats, setStats] = useState({
    products: 0,
    orders: 0,
    users: 0,
    categories: 0,
    revenue: 0,
  });
  const [orderStatusCounts, setOrderStatusCounts] = useState({
    total: 0,
    pending: 0,
    called: 0,
    confirmed: 0,
    processing: 0,
    shipped: 0,
    delivered: 0,
    cancelled: 0,
    returned: 0,
  });
  const [expenseSummary, setExpenseSummary] = useState({
    total_expense: 0,
    total_paid: 0,
    total_due: 0,
  });
  const [loading, setLoading] = useState(true);
  const [countsLoading, setCountsLoading] = useState(true);

  const loadStats = async () => {
    try {
      const [productData, orderData, userData, categoryData] = await Promise.all([
        adminGetProducts({ limit: 1 }),
        adminGetOrders({ limit: 100 }),
        adminGetUsers({ limit: 1, exclude_role: 'admin' }),
        adminGetCategories({ limit: 1 }),
      ]);

      const orders = orderData.orders || [];
      const revenue = orders
        .filter((o) => o.status === 'delivered')
        .reduce((sum, o) => sum + parseFloat(o.total_price || '0'), 0);

      setStats({
        products: productData.total || 0,
        orders: orderData.total || orders.length,
        users: userData.total || 0,
        categories: categoryData.total || 0,
        revenue,
      });
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
      addToast('Failed to load dashboard data.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadCounts = async () => {
    try {
      const [orderCounts, expenseData] = await Promise.all([
        adminGetOrderStatusCounts(),
        adminGetExpenseSummary({ period: 'all' }),
      ]);

      setOrderStatusCounts({
        total: orderCounts.total || 0,
        pending: orderCounts.pending || 0,
        called: orderCounts.called || 0,
        confirmed: orderCounts.confirmed || 0,
        processing: orderCounts.processing || 0,
        shipped: orderCounts.shipped || 0,
        delivered: orderCounts.delivered || 0,
        cancelled: orderCounts.cancelled || 0,
        returned: orderCounts.returned || 0,
      });
      setExpenseSummary({
        total_expense: expenseData.total_expense || 0,
        total_paid: expenseData.total_paid || 0,
        total_due: expenseData.total_due || 0,
      });
    } catch (error) {
      console.error('Failed to load dashboard counts:', error);
      addToast('Failed to load live counts.', 'error');
    } finally {
      setCountsLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
    loadCounts();

    const interval = setInterval(loadCounts, 15000);

    const handleOrderStatusUpdate = () => loadCounts();
    const handleExpenseUpdate = () => loadCounts();

    window.addEventListener('order-status-updated', handleOrderStatusUpdate);
    window.addEventListener('expense-updated', handleExpenseUpdate);

    return () => {
      clearInterval(interval);
      window.removeEventListener('order-status-updated', handleOrderStatusUpdate);
      window.removeEventListener('expense-updated', handleExpenseUpdate);
    };
  }, []);

  const statCards = [
    { label: 'Total Products', value: stats.products, icon: <FaBox />, color: 'blue', link: '/admin/products' },
    { label: 'Total Users', value: stats.users, icon: <FaUsers />, color: 'purple', link: '/admin/users' },
    { label: 'Categories', value: stats.categories, icon: <FaTags />, color: 'teal', link: '/admin/categories' },
    { label: 'Revenue (৳)', value: stats.revenue.toLocaleString(), icon: <FaMoneyBillWave />, color: 'red', link: '/admin/orders' },
  ];

  const orderStatusCards = [
    { label: 'Total Orders', value: orderStatusCounts.total, icon: <FaShoppingBag />, color: 'green', link: '/admin/orders' },
    { label: 'Pending Orders', value: orderStatusCounts.pending, icon: <FaClock />, color: 'orange', link: '/admin/orders?status=pending' },
    { label: 'Called for Confirmation', value: orderStatusCounts.called, icon: <FaPhoneAlt />, color: 'yellow', link: '/admin/orders?status=called' },
    { label: 'Confirmed Orders', value: orderStatusCounts.confirmed, icon: <FaCheckCircle />, color: 'blue', link: '/admin/orders?status=confirmed' },
    { label: 'Processing', value: orderStatusCounts.processing, icon: <FaCogs />, color: 'purple', link: '/admin/orders?status=processing' },
    { label: 'Shipped', value: orderStatusCounts.shipped, icon: <FaTruck />, color: 'teal', link: '/admin/orders?status=shipped' },
    { label: 'Delivered', value: orderStatusCounts.delivered, icon: <FaBoxOpen />, color: 'indigo', link: '/admin/orders?status=delivered' },
    { label: 'Cancelled', value: orderStatusCounts.cancelled, icon: <FaBan />, color: 'gray', link: '/admin/orders?status=cancelled' },
    { label: 'Returned', value: orderStatusCounts.returned, icon: <FaUndo />, color: 'pink', link: '/admin/orders?status=returned' },
  ];

  const expenseCards = [
    { label: 'Total Expense', value: `৳${expenseSummary.total_expense.toLocaleString()}`, icon: <FaMoneyBillWave />, color: 'red', link: '/admin/expenses' },
    { label: 'Paid', value: `৳${expenseSummary.total_paid.toLocaleString()}`, icon: <FaMoneyCheck />, color: 'green', link: '/admin/expenses?status=paid' },
    { label: 'Due', value: `৳${expenseSummary.total_due.toLocaleString()}`, icon: <FaMoneyCheck />, color: 'orange', link: '/admin/expenses?status=due' },
  ];

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  return (
    <div className="admin-dashboard">
      <h2>Dashboard Overview</h2>

      <div className="stats-grid">
        {statCards.map((card, index) => (
          <Link to={card.link} className={`stat-card stat-${card.color}`} key={index}>
            <div className="stat-icon">{card.icon}</div>
            <div className="stat-info">
              <span className="stat-value">{card.value}</span>
              <span className="stat-label">{card.label}</span>
            </div>
          </Link>
        ))}
      </div>

      <h3 className="dashboard-section-title">Order Status</h3>
      <div className="stats-grid">
        {orderStatusCards.map((card, index) => (
          <Link to={card.link} className={`stat-card stat-${card.color}`} key={index}>
            <div className="stat-icon">{card.icon}</div>
            <div className="stat-info">
              <span className="stat-value">{countsLoading ? '...' : card.value}</span>
              <span className="stat-label">{card.label}</span>
            </div>
          </Link>
        ))}
      </div>

      <h3 className="dashboard-section-title">Expense Overview</h3>
      <div className="stats-grid">
        {expenseCards.map((card, index) => (
          <Link to={card.link} className={`stat-card stat-${card.color}`} key={index}>
            <div className="stat-icon">{card.icon}</div>
            <div className="stat-info">
              <span className="stat-value">{countsLoading ? '...' : card.value}</span>
              <span className="stat-label">{card.label}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default AdminDashboard;
