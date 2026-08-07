import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { FaUserShield, FaLock, FaPhoneAlt, FaArrowLeft } from 'react-icons/fa';
import { adminLogin } from '../../api/services';

function AdminLogin() {
  const navigate = useNavigate();
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!phone.trim() || !password) {
      setError('Please enter both phone number and password.');
      return;
    }

    try {
      setLoading(true);
      const data = await adminLogin(phone.trim(), password);
      localStorage.setItem('admin_token', data.access_token);
      navigate('/admin/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-login-page">
      <div className="admin-login-box">
        <div className="admin-login-header">
          <FaUserShield className="admin-login-icon" />
          <h1>Admin Login</h1>
          <p>Wave Notebook Admin Panel</p>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="admin-phone">
              <FaPhoneAlt /> Phone Number
            </label>
            <input
              type="tel"
              id="admin-phone"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="01XXXXXXXXX"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="admin-password">
              <FaLock /> Password
            </label>
            <input
              type="password"
              id="admin-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>

          <button type="submit" className="btn btn-primary btn-lg" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <Link to="/" className="back-to-site">
          <FaArrowLeft /> Back to Website
        </Link>
      </div>
    </div>
  );
}

export default AdminLogin;