import { Link } from 'react-router-dom';
import { FaFacebook, FaInstagram, FaYoutube, FaPhoneAlt, FaEnvelope, FaMapMarkerAlt } from 'react-icons/fa';

function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-grid">
        <div className="footer-col">
          <h3 className="footer-title">Wave Notebook</h3>
          <p className="footer-desc">
            Your trusted online shop for quality notebooks, stationery and school supplies.
            Fast delivery all over Bangladesh.
          </p>
          <div className="footer-social">
            <a href="#" className="social-link"><FaFacebook /></a>
            <a href="#" className="social-link"><FaInstagram /></a>
            <a href="#" className="social-link"><FaYoutube /></a>
          </div>
        </div>

        <div className="footer-col">
          <h3 className="footer-title">Quick Links</h3>
          <ul className="footer-links">
            <li><Link to="/">Home</Link></li>
            <li><Link to="/products">All Products</Link></li>
            <li><Link to="/cart">Cart</Link></li>
            <li><Link to="/track-order">Track Order</Link></li>
          </ul>
        </div>

        <div className="footer-col">
          <h3 className="footer-title">Categories</h3>
          <ul className="footer-links">
            <li><Link to="/products">Notebooks</Link></li>
            <li><Link to="/products">Stationery</Link></li>
            <li><Link to="/products">School Supplies</Link></li>
            <li><Link to="/products">Office Supplies</Link></li>
          </ul>
        </div>

        <div className="footer-col">
          <h3 className="footer-title">Contact Us</h3>
          <ul className="footer-contact">
            <li><FaPhoneAlt className="footer-contact-icon" /> 01700-000000</li>
            <li><FaEnvelope className="footer-contact-icon" /> support@wavenotebook.com</li>
            <li><FaMapMarkerAlt className="footer-contact-icon" /> Dhaka, Bangladesh</li>
          </ul>
        </div>
      </div>

      <div className="footer-bottom">
        <div className="container">
          <p>&copy; {new Date().getFullYear()} Wave Notebook. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}

export default Footer;