import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FaBox,
  FaShoppingBag,
  FaUsers,
  FaTags,
  FaMoneyBillWave,
  FaClipboardList,
} from 'react-icons/fa';
import {
  adminGetProducts,
  adminGetOrders,
  adminGetUsers,
  adminGetCategories,
} from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';

function AdminDashboard() {
  const { addToast } = useToast();
  const [stats, setStats] = useState({
    products: 0,
    orders: 0,
    users: 0,
    categories: 0,
    pendingOrders: 0,
    revenue: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const [productData, orderData, userData, categoryData] = await Promise.all([
          adminGetProducts({ limit: 1 }),
          adminGetOrders({ limit: 100 }),
          adminGetUsers({ limit: 1 }),
          adminGetCategories({ limit: 1 }),
        ]);

        const orders = orderData.orders || [];
        const pendingOrders = orders.filter((o) => o.status === 'pending');
        const revenue = orders
          .filter((o) => o.status === 'delivered')
          .reduce((sum, o) => sum + parseFloat(o.total_price || '0'), 0);

        setStats({
          products: productData.total || 0,
          orders: orderData.total || orders.length,
          users: userData.total || 0,
          categories: categoryData.total || 0,
          pendingOrders: pendingOrders.length,
          revenue,
        });
      } catch (error) {
        console.error('Failed to load dashboard stats:', error);
        addToast('Failed to load dashboard data.', 'error');
      } finally {
        setLoading(false);
      }
    };
    loadStats();
  }, []);

  const statCards = [
    { label: 'Total Products', value: stats.products, icon: <FaBox />, color: 'blue', link: '/admin/products' },
    { label: 'Total Orders', value: stats.orders, icon: <FaShoppingBag />, color: 'green', link: '/admin/orders' },
    { label: 'Pending Orders', value: stats.pendingOrders, icon: <FaClipboardList />, color: 'orange', link: '/admin/orders?status=pending' },
    { label: 'Total Users', value: stats.users, icon: <FaUsers />, color: 'purple', link: '/admin/users' },
    { label: 'Categories', value: stats.categories, icon: <FaTags />, color: 'teal', link: '/admin/categories' },
    { label: 'Revenue (৳)', value: stats.revenue.toLocaleString(), icon: <FaMoneyBillWave />, color: 'red', link: '/admin/orders' },
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
    </div>
  );
}

export default AdminDashboard;