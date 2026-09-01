import { Link } from 'react-router-dom';
import { FaFacebook, FaInstagram, FaYoutube, FaTwitter, FaPaperPlane } from 'react-icons/fa';
import { useSiteSettings } from '../context/SiteSettingsContext';

function Footer() {
  const { settings, loading: settingsLoading } = useSiteSettings();

  const socialLinks = [
    { key: 'facebook_url', icon: <FaFacebook />, name: 'Facebook' },
    { key: 'youtube_url', icon: <FaYoutube />, name: 'YouTube' },
    { key: 'instagram_url', icon: <FaInstagram />, name: 'Instagram' },
    { key: 'twitter_url', icon: <FaTwitter />, name: 'Twitter' },
  ];

  const visibleSocial = socialLinks.filter((s) => settings[s.key]);

  return (
    <footer className="footer">
      <div className="container">
        {/* Centered Brand Header */}
        <div className="footer-brand">
          {/* Skeleton while settings load — never show the default site name */}
          {settingsLoading ? (
            <>
              <h3 className="footer-brand-name" aria-hidden="true">
                <span className="skeleton skeleton-on-dark skeleton-footer-name" />
              </h3>
              <p className="footer-desc" aria-hidden="true">
                <span className="skeleton skeleton-on-dark skeleton-footer-desc" />
              </p>
            </>
          ) : (
            <>
              <h3 className="footer-brand-name">
                {(settings.site_name || 'Wave Notebook').split(' ')[0]}{' '}
                <span>{(settings.site_name || 'Wave Notebook').split(' ').slice(1).join(' ')}</span>
              </h3>
              {settings.site_description && (
                <p className="footer-desc">{settings.site_description}</p>
              )}
            </>
          )}
        </div>

        {/* Fading Separator */}
        <div className="footer-separator" />

        {/* Navigation Columns */}
        <div className="footer-nav">
        <div className="footer-col">
          <h3 className="footer-title">Quick Links</h3>
          <ul className="footer-links">
            <li><Link to="/">Home</Link></li>
            <li><Link to="/products">All Products</Link></li>
            <li><Link to="/cart">Cart</Link></li>
            <li><Link to="/track-order">Track Order</Link></li>
            <li><Link to="/contact">Contact Us</Link></li>
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

        {/* Contact Us CTA */}
        <div className="footer-col">
          <h3 className="footer-title">Contact Us</h3>
          <p className="footer-contact-lead">
            Questions, feedback or orders — we would love to hear from you.
          </p>
          <Link to="/contact" className="footer-contact-card">
            <div className="fcc-icon">
              <FaPaperPlane />
            </div>
            <div className="fcc-body">
              <div className="fcc-top">
                <span className="fcc-big">Send us a message</span>
                <span className="fcc-arrow">→</span>
              </div>
              <span className="fcc-sub">We usually reply within 24 hours</span>
            </div>
          </Link>
        </div>
        </div>
      </div>

      <div className="footer-bottom">
        <div className="container footer-bottom-inner">
          {settingsLoading ? (
            <span className="skeleton skeleton-on-dark skeleton-footer-copy" aria-hidden="true" />
          ) : (
            <p>&copy; {new Date().getFullYear()} {settings.site_name || 'Wave Notebook'}. All rights reserved.</p>
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

          <p className="footer-made">
            Crafted with <span>♥</span> for notebook lovers
          </p>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
