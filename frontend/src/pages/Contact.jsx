import { useState } from 'react';
import {
  FaPaperPlane,
  FaMapMarkerAlt,
  FaEnvelope,
  FaPhoneAlt,
  FaCheckCircle,
} from 'react-icons/fa';
import { sendMessage } from '../api/services';
import { useSiteSettings } from '../context/SiteSettingsContext';
import { useToast } from '../context/ToastContext';
import PhoneInput, { getPhoneInputIssue } from '../components/PhoneInput';

function Contact() {
  const { settings, loading: settingsLoading } = useSiteSettings();
  const { addToast } = useToast();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone_number: '',
    message: '',
  });
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const handlePhoneChange = (name, value) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const validate = () => {
    const errs = {};
    if (!formData.name.trim() || formData.name.trim().length < 2) {
      errs.name = 'Please enter your full name.';
    }
    if (!formData.email.trim()) {
      errs.email = 'Please enter your email address.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      errs.email = 'Please enter a valid email address.';
    }
    if (!formData.phone_number.trim()) {
      errs.phone_number = 'Please enter your phone number.';
    } else if (formData.phone_number.replace(/\D/g, '').length < 6) {
      errs.phone_number = 'Please enter a valid phone number.';
    }
    if (!formData.message.trim() || formData.message.trim().length < 5) {
      errs.message = 'Please write a message.';
    }
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }
    // Country-code duplication (leading 0 / repeated code) — the live inline
    // error already shows under the phone box; block submit with a toast.
    const phoneIssue = getPhoneInputIssue(formData.phone_number);
    if (phoneIssue) {
      addToast(phoneIssue, 'error');
      return;
    }

    try {
      setSending(true);
      await sendMessage({
        name: formData.name.trim(),
        email: formData.email.trim(),
        phone_number: formData.phone_number.trim(),
        message: formData.message.trim(),
      });
      setSent(true);
      setFormData({ name: '', email: '', phone_number: '', message: '' });
      addToast('Your message has been sent successfully!', 'success');
    } catch (err) {
      addToast(
        err.response?.data?.detail || 'Failed to send your message. Please try again.',
        'error'
      );
    } finally {
      setSending(false);
    }
  };

  const infoCards = [
    {
      icon: <FaMapMarkerAlt />,
      title: 'Office Address',
      value: settings.contact_address,
      href: null,
    },
    {
      icon: <FaEnvelope />,
      title: 'Mail Address',
      value: settings.contact_email,
      href: settings.contact_email ? `mailto:${settings.contact_email}` : null,
    },
    {
      icon: <FaPhoneAlt />,
      title: 'Phone Number',
      value: settings.hotline_number || settings.contact_phone,
      href:
        (settings.hotline_number || settings.contact_phone)
          ? `tel:${(settings.hotline_number || settings.contact_phone).replace(/[^+\d]/g, '')}`
          : null,
    },
  ];

  return (
    <ContactView
      sent={sent}
      setSent={setSent}
      sending={sending}
      errors={errors}
      infoCards={infoCards}
      infoLoading={settingsLoading}
      handleSubmit={handleSubmit}
      handleChange={handleChange}
      handlePhoneChange={handlePhoneChange}
      formData={formData}
    />
  );
}

export default Contact;

// ==========================================
// View Component
// ==========================================
function ContactView({
  sent,
  setSent,
  sending,
  errors,
  infoCards,
  infoLoading,
  handleSubmit,
  handleChange,
  handlePhoneChange,
  formData,
}) {
  return (
    <div className="contact-page">
      {/* Page Header */}
      <div className="contact-hero">
        <div className="container">
          <h1 className="contact-title">Get In Touch</h1>
          <p className="contact-subtitle">
            Have a question or want to leave us a message? Fill out the form
            below and we will get back to you as soon as possible.
          </p>
        </div>
      </div>

      <div className="container contact-content">
        {/* Message Form */}
        <div className="contact-form-card">
          {sent ? (
            <div className="contact-success">
              <FaCheckCircle className="contact-success-icon" />
              <h2>Message Sent!</h2>
              <p>Thank you for reaching out. We will get back to you soon.</p>
              <button
                type="button"
                className="btn btn-outline contact-send-again"
                onClick={() => setSent(false)}
              >
                Send Another Message
              </button>
            </div>
          ) : (
            <>
              <h2 className="contact-form-title">Leave a Message</h2>
              <form onSubmit={handleSubmit} noValidate>
                <div className="contact-form-grid">
                  <div className="contact-field">
                    <label htmlFor="name">
                      Full Name <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      id="name"
                      name="name"
                      placeholder="Your full name"
                      value={formData.name}
                      onChange={handleChange}
                      autoComplete="name"
                    />
                    {errors.name && <span className="field-error">{errors.name}</span>}
                  </div>

                  <div className="contact-field">
                    <label htmlFor="email">
                      Email Address <span className="required">*</span>
                    </label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      placeholder="you@example.com"
                      value={formData.email}
                      onChange={handleChange}
                      autoComplete="email"
                    />
                    {errors.email && <span className="field-error">{errors.email}</span>}
                  </div>

                  <div className="contact-field full-width">
                    <label htmlFor="phone_number">
                      Phone Number <span className="required">*</span>
                    </label>
                    <PhoneInput
                      name="phone_number"
                      value={formData.phone_number}
                      onChange={handlePhoneChange}
                      placeholder="1XXX XXXXXX"
                      className="contact-phone-input"
                    />
                    {errors.phone_number && (
                      <span className="field-error">{errors.phone_number}</span>
                    )}
                  </div>

                  <div className="contact-field full-width">
                    <label htmlFor="message">
                      Your Message <span className="required">*</span>
                    </label>
                    <textarea
                      id="message"
                      name="message"
                      rows={6}
                      placeholder="Write your message here..."
                      value={formData.message}
                      onChange={handleChange}
                    />
                    {errors.message && (
                      <span className="field-error">{errors.message}</span>
                    )}
                  </div>
                </div>

                <button
                  type="submit"
                  className="btn btn-primary contact-submit-btn"
                  disabled={sending}
                >
                  <FaPaperPlane />
                  {sending ? 'Sending...' : 'Send Message'}
                </button>
              </form>
            </>
          )}
        </div>
      </div>

      {/* Contact Info Cards */}
      <div className="container contact-info-section">
        <div className="contact-info-grid">
          {infoLoading
            ? /* Skeleton cards while settings load — never empty/fake cards */
              Array.from({ length: 3 }).map((_, index) => (
                <div key={index} className="contact-info-card" aria-hidden="true">
                  <div className="skeleton skeleton-contact-icon" />
                  <div className="skeleton skeleton-contact-line" />
                  <div className="skeleton skeleton-contact-line" style={{ width: '50%' }} />
                </div>
              ))
            : infoCards.map(
                (card, index) =>
                  card.value && (
                    <div key={index} className="contact-info-card">
                      <div className="contact-info-icon">{card.icon}</div>
                      <h3 className="contact-info-title">{card.title}</h3>
                      {card.href ? (
                        <a href={card.href} className="contact-info-value">
                          {card.value}
                        </a>
                      ) : (
                        <p className="contact-info-value">{card.value}</p>
                      )}
                    </div>
                  )
              )}
        </div>
      </div>
    </div>
  );
}