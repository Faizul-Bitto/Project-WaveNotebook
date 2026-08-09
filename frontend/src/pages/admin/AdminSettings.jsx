import { useEffect, useState } from 'react';
import { FaSave } from 'react-icons/fa';
import { adminGetSettings, adminUpdateSettings } from '../../api/adminServices';
import { useSiteSettings } from '../../context/SiteSettingsContext';

function AdminSettings() {
  const { refresh } = useSiteSettings();
  const [formData, setFormData] = useState({
    site_name: 'WaveNotebook',
    site_description: '',
    contact_phone: '',
    contact_email: '',
    contact_address: '',
    facebook_url: '',
    youtube_url: '',
    instagram_url: '',
    twitter_url: '',
    privacy_policy: '',
    terms_conditions: '',
    refund_policy: '',
  });
  const [logoUrl, setLogoUrl] = useState('');
  const [logoFile, setLogoFile] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const data = await adminGetSettings();
        const s = data.settings || {};
        setFormData({
          site_name: s.site_name || 'WaveNotebook',
          site_description: s.site_description || '',
          contact_phone: s.contact_phone || '',
          contact_email: s.contact_email || '',
          contact_address: s.contact_address || '',
          facebook_url: s.facebook_url || '',
          youtube_url: s.youtube_url || '',
          instagram_url: s.instagram_url || '',
          twitter_url: s.twitter_url || '',
          privacy_policy: s.privacy_policy || '',
          terms_conditions: s.terms_conditions || '',
          refund_policy: s.refund_policy || '',
        });
        setLogoUrl(s.logo_url || '');
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load settings.');
      }
    };
    loadSettings();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleLogoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setLogoFile(file);
      setLogoUrl(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    try {
      setSaving(true);
      const fd = new FormData();
      fd.append('site_name', formData.site_name);
      fd.append('site_description', formData.site_description);
      fd.append('contact_phone', formData.contact_phone);
      fd.append('contact_email', formData.contact_email);
      fd.append('contact_address', formData.contact_address);
      fd.append('facebook_url', formData.facebook_url);
      fd.append('youtube_url', formData.youtube_url);
      fd.append('instagram_url', formData.instagram_url);
      fd.append('twitter_url', formData.twitter_url);
      fd.append('privacy_policy', formData.privacy_policy);
      fd.append('terms_conditions', formData.terms_conditions);
      fd.append('refund_policy', formData.refund_policy);
      if (logoFile) fd.append('logo', logoFile);
      await adminUpdateSettings(fd);
      await refresh();
      setSuccess('Settings saved successfully!');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save settings.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="admin-page">
      <h2>Site Settings</h2>
      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <form onSubmit={handleSubmit}>
        {/* Logo & Branding */}
        <div className="admin-form">
          <h3>Logo & Branding</h3>

          {logoUrl && (
            <div style={{ marginBottom: '16px', textAlign: 'center' }}>
              <img
                src={logoUrl}
                alt="Site Logo"
                style={{ height: '60px', maxWidth: '200px', objectFit: 'contain', background: '#f3f4f6', padding: '8px', borderRadius: '8px' }}
              />
            </div>
          )}

          <div className="form-group">
            <label>Site Name</label>
            <input type="text" name="site_name" value={formData.site_name} onChange={handleChange} placeholder="WaveNotebook" />
          </div>

          <div className="form-group">
            <label>Site Description (for footer)</label>
            <textarea
              name="site_description"
              value={formData.site_description}
              onChange={handleChange}
              placeholder="Your trusted online shop for quality notebooks, stationery and school supplies. Fast delivery all over Bangladesh."
              rows="3"
            />
          </div>

          <div className="form-group">
            <label>Upload Logo</label>
            <input type="file" accept="image/*" onChange={handleLogoChange} />
            <p className="upload-hint">Upload a logo (PNG, JPG)</p>
          </div>
        </div>

        {/* Contact Information */}
        <div className="admin-form">
          <h3>Contact Information</h3>

          <div className="form-group">
            <label>Phone</label>
            <input type="text" name="contact_phone" value={formData.contact_phone} onChange={handleChange} placeholder="01700-000000" />
          </div>

          <div className="form-group">
            <label>Email</label>
            <input type="email" name="contact_email" value={formData.contact_email} onChange={handleChange} placeholder="support@wavenotebook.com" />
          </div>

          <div className="form-group">
            <label>Address</label>
            <input type="text" name="contact_address" value={formData.contact_address} onChange={handleChange} placeholder="Dhaka, Bangladesh" />
          </div>
        </div>

        {/* Social Media Links */}
        <div className="admin-form">
          <h3>Social Media Links</h3>
          <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '16px' }}>Leave empty to hide the icon from the footer.</p>

          <div className="form-group">
            <label>Facebook URL</label>
            <input type="url" name="facebook_url" value={formData.facebook_url} onChange={handleChange} placeholder="https://facebook.com/..." />
          </div>

          <div className="form-group">
            <label>YouTube URL</label>
            <input type="url" name="youtube_url" value={formData.youtube_url} onChange={handleChange} placeholder="https://youtube.com/..." />
          </div>

          <div className="form-group">
            <label>Instagram URL</label>
            <input type="url" name="instagram_url" value={formData.instagram_url} onChange={handleChange} placeholder="https://instagram.com/..." />
          </div>

          <div className="form-group">
            <label>Twitter URL</label>
            <input type="url" name="twitter_url" value={formData.twitter_url} onChange={handleChange} placeholder="https://twitter.com/..." />
          </div>
        </div>

        {/* Policy Pages */}
        <div className="admin-form">
          <h3>Policy Pages</h3>
          <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '16px' }}>Content written here will appear on the respective policy pages.</p>

          <div className="form-group">
            <label>Privacy Policy</label>
            <textarea
              name="privacy_policy"
              value={formData.privacy_policy}
              onChange={handleChange}
              placeholder="Write your privacy policy here..."
              rows="6"
            />
          </div>

          <div className="form-group">
            <label>Terms & Conditions</label>
            <textarea
              name="terms_conditions"
              value={formData.terms_conditions}
              onChange={handleChange}
              placeholder="Write your terms and conditions here..."
              rows="6"
            />
          </div>

          <div className="form-group">
            <label>Refund & Return Policy</label>
            <textarea
              name="refund_policy"
              value={formData.refund_policy}
              onChange={handleChange}
              placeholder="Write your refund and return policy here..."
              rows="6"
            />
          </div>
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={saving}>
            <FaSave /> {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default AdminSettings;
