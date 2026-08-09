import { Link } from 'react-router-dom';
import { FaFacebook, FaInstagram, FaYoutube, FaTwitter, FaPhoneAlt, FaEnvelope, FaMapMarkerAlt } from 'react-icons/fa';
import { useSiteSettings } from '../context/SiteSettingsContext';

function Footer() {
  const { settings } = useSiteSettings();

  const socialLinks = [
    { key: 'facebook_url', icon: <FaFacebook />, name: 'Facebook' },
    { key: 'youtube_url', icon: <FaYoutube />, name: 'YouTube' },
    { key: 'instagram_url', icon: <FaInstagram />, name: 'Instagram' },
    { key: 'twitter_url', icon: <FaTwitter />, name: 'Twitter' },
  ];

  const visibleSocial = socialLinks.filter((s) => settings[s.key]);

  return (
    <footer className="footer">
      <div className="container footer-grid">
        {/* Brand & Description */}
        <div className="footer-col">
          <h3 className="footer-title">{settings.site_name || 'Wave Notebook'}</h3>
          {settings.site_description && (
            <p className="footer-desc">{settings.site_description}</p>
          )}
          {visibleSocial.length > 0 && (
            <div className="footer-social">
              {visibleSocial.map((social) => (
                <a
                  key={social.key}
                  href={settings[social.key]}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="social-link"
                  aria-label={social.name}
                >
                  {social.icon}
                </a>
              ))}
            </div>
          )}
        </div>

        {/* Quick Links */}
        <div className="footer-col">
          <h3 className="footer-title">Quick Links</h3>
          <ul className="footer-links">
            <li><Link to="/">Home</Link></li>
            <li><Link to="/products">All Products</Link></li>
            <li><Link to="/cart">Cart</Link></li>
            <li><Link to="/track-order">Track Order</Link></li>
          </ul>
        </div>

        {/* Policy Pages */}
        <div className="footer-col">
          <h3 className="footer-title">Policies</h3>
          <ul className="footer-links">
            <li><Link to="/privacy-policy">Privacy Policy</Link></li>
            <li><Link to="/terms-conditions">Terms & Conditions</Link></li>
            <li><Link to="/refund-policy">Refund & Return Policy</Link></li>
          </ul>
        </div>

        {/* Contact */}
        <div className="footer-col">
          <h3 className="footer-title">Contact Us</h3>
          <ul className="footer-contact">
            {settings.contact_phone && (
              <li><FaPhoneAlt className="footer-contact-icon" /> {settings.contact_phone}</li>
            )}
            {settings.contact_email && (
              <li><FaEnvelope className="footer-contact-icon" /> {settings.contact_email}</li>
            )}
            {settings.contact_address && (
              <li><FaMapMarkerAlt className="footer-contact-icon" /> {settings.contact_address}</li>
            )}
          </ul>
        </div>
      </div>

      <div className="footer-bottom">
        <div className="container">
          <p>&copy; {new Date().getFullYear()} {settings.site_name || 'Wave Notebook'}. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
