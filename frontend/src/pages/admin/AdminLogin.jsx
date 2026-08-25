import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { FaUserShield, FaLock, FaArrowLeft, FaEye, FaEyeSlash } from 'react-icons/fa';
import { adminLogin } from '../../api/services';
import { useToast } from '../../context/ToastContext';
import { validateForm, clearFieldError, firstError } from '../../utils/validation';
import PhoneInput from '../../components/PhoneInput';

function AdminLogin() {
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const handlePhoneChange = (name, val) => {
    setPhone(val);
    setErrors((prev) => clearFieldError(prev, 'phone'));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();


    const rawPhone = phone.trim();

    const errs = validateForm({ phone: rawPhone, password }, {
      phone: { label: 'phone number', required: true },
      password: { label: 'password', required: true },
    });
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      addToast(firstError(errs), 'error');
      return;
    }
    setErrors({});

    try {
      setLoading(true);
      const data = await adminLogin(rawPhone, password);
      localStorage.setItem('admin_token', data.access_token);
      navigate('/admin/dashboard');
      addToast('Login successful!', 'success');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Login failed. Please check your credentials.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-login-page">
      <div className="admin-login-box">
        <div className="admin-login-badge">
          <FaUserShield />
        </div>

        <div className="admin-login-header">
          <h1>Admin Login</h1>
          <p>Wave Notebook Admin Panel</p>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <div className={`admin-field ${errors.phone ? 'field-invalid' : ''}`}>
            <label htmlFor="admin-phone">Phone Number</label>
            <PhoneInput
              name="admin-phone"
              value={phone}
              onChange={handlePhoneChange}
              placeholder="1XXXXXXXXX"
            />
            {errors.phone && <span className="field-error">{errors.phone}</span>}
          </div>

          <div className={`admin-field ${errors.password ? 'field-invalid' : ''}`}>
            <label htmlFor="admin-password">Password</label>
            <div className="admin-password-wrap">
              <input
                type={showPassword ? 'text' : 'password'}
                id="admin-password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setErrors((prev) => clearFieldError(prev, 'password'));
                }}
                placeholder="Enter your password"
                autoComplete="current-password"
              />
              <button
                type="button"
                className="admin-password-toggle"
                onClick={() => setShowPassword((s) => !s)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <FaEyeSlash /> : <FaEye />}
              </button>
            </div>
            {errors.password && <span className="field-error">{errors.password}</span>}
          </div>

          <button type="submit" className="admin-login-btn" disabled={loading}>
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