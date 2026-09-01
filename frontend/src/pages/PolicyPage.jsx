import { Link, useLocation } from 'react-router-dom';
import { useSiteSettings } from '../context/SiteSettingsContext';

const today = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

const policyConfig = {
  'privacy-policy': {
    title: 'Privacy Policy',
    settingKey: 'privacy_policy',
    defaultContent:
      '<h2>Privacy Policy</h2>' +
      '<p>Last updated: ' + today + '</p>' +
      '<h3>1. Information We Collect</h3>' +
      '<p>We collect information you provide directly to us, including information you provide when you create an account, place an order, or contact us.</p>' +
      '<h3>2. How We Use Your Information</h3>' +
      '<p>We use the information we collect to provide, maintain, and improve our services, process transactions, and communicate with you.</p>' +
      '<h3>3. Information Sharing</h3>' +
      '<p>We do not sell, trade, or otherwise transfer your personally identifiable information to outside parties, except as described in this policy.</p>' +
      '<h3>4. Cookies</h3>' +
      '<p>We may use cookies to enhance your browsing experience and understand how our site is used.</p>' +
      '<h3>5. Security</h3>' +
      '<p>We strive to protect your personal information and use commercially acceptable means to do so.</p>' +
      '<h3>6. Changes to This Policy</h3>' +
      '<p>We may update this privacy policy from time to time. Any changes will be posted on this page.</p>' +
      '<h3>7. Contact Us</h3>' +
      '<p>If you have any questions about this Privacy Policy, please contact us.</p>',
  },
  'terms-conditions': {
    title: 'Terms & Conditions',
    settingKey: 'terms_conditions',
    defaultContent:
      '<h2>Terms & Conditions</h2>' +
      '<p>Last updated: ' + today + '</p>' +
      '<h3>1. Acceptance of Terms</h3>' +
      '<p>By accessing or using our website, you agree to be bound by these Terms & Conditions.</p>' +
      '<h3>2. Products & Services</h3>' +
      '<p>We strive to provide accurate information about our products. All prices are subject to change without notice.</p>' +
      '<h3>3. Orders</h3>' +
      '<p>When you place an order, you are offering to purchase the products listed. We reserve the right to refuse or cancel any order.</p>' +
      '<h3>4. Payment</h3>' +
      '<p>All payments are processed securely. We accept various payment methods as listed on our checkout page.</p>' +
      '<h3>5. Shipping & Delivery</h3>' +
      '<p>We deliver to addresses within Bangladesh. Delivery times are estimates and not guaranteed.</p>' +
      '<h3>6. Returns & Refunds</h3>' +
      '<p>Please refer to our Refund & Return Policy for information about returns and refunds.</p>' +
      '<h3>7. Limitation of Liability</h3>' +
      '<p>We shall not be liable for any indirect, incidental, or consequential damages arising from your use of our services.</p>' +
      '<h3>8. Governing Law</h3>' +
      '<p>These terms are governed by the laws of Bangladesh.</p>' +
      '<h3>9. Contact Us</h3>' +
      '<p>If you have any questions about these Terms, please contact us.</p>',
  },
  'refund-policy': {
    title: 'Refund & Return Policy',
    settingKey: 'refund_policy',
    defaultContent:
      '<h2>Refund & Return Policy</h2>' +
      '<p>Last updated: ' + today + '</p>' +
      '<h3>1. Return Policy</h3>' +
      '<p>You may return most items within 7 days of delivery for a full refund. Items must be unused and in their original packaging.</p>' +
      '<h3>2. Eligibility for Returns</h3>' +
      '<p>To be eligible for a return, your item must be unused, in the same condition as received, and in the original packaging.</p>' +
      '<h3>3. Non-Returnable Items</h3>' +
      '<p>Certain items are not eligible for return, including but not limited to: opened/used notebooks, personalized items, and digital downloads.</p>' +
      '<h3>4. Refund Process</h3>' +
      '<p>Once we receive your returned item, we will inspect it and notify you of the status of your refund. If approved, we will process your refund to your original payment method.</p>' +
      '<h3>5. Shipping Costs</h3>' +
      '<p>You are responsible for paying the shipping costs for returning your item. Original shipping charges are non-refundable.</p>' +
      '<h3>6. Late or Missing Refunds</h3>' +
      "<p>If you haven't received a refund after we've processed it, please contact your bank or card issuer first, then contact us.</p>" +
      '<h3>7. Contact Us</h3>' +
      '<p>If you have any questions about our Refund Policy, please contact us.</p>',
  },
};

function PolicyPage() {
  const location = useLocation();
  const { settings, loading: settingsLoading } = useSiteSettings();
  const slug = location.pathname.replace(/^\//, '');
  const config = policyConfig[slug];

  if (!config) {
    return (
      <div className="container empty-state">
        <h2>Page Not Found</h2>
        <p>The page you are looking for does not exist.</p>
        <Link to="/" className="btn btn-primary">Go Home</Link>
      </div>
    );
  }

  // While settings load, show a skeleton — never the default policy text.
  // The defaultContent fallback below is only used once loading has settled
  // and the API truly has no custom content for this policy.
  if (settingsLoading) {
    return (
      <div className="policy-page">
        <div className="container">
          <div className="policy-content" aria-hidden="true">
            <span className="skeleton skeleton-policy-heading" />
            <span className="skeleton skeleton-policy-line" />
            <span className="skeleton skeleton-policy-line" />
            <span className="skeleton skeleton-policy-line" style={{ width: '85%' }} />
            <span className="skeleton skeleton-policy-heading" />
            <span className="skeleton skeleton-policy-line" style={{ width: '92%' }} />
            <span className="skeleton skeleton-policy-line" style={{ width: '78%' }} />
          </div>
        </div>
      </div>
    );
  }

  const content = settings[config.settingKey] || config.defaultContent;

  return (
    <div className="policy-page">
      <div className="container">
        <div className="policy-content" dangerouslySetInnerHTML={{ __html: content }} />
      </div>
    </div>
  );
}

export default PolicyPage;
