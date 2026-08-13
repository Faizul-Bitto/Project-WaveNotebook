import { FaWhatsapp, FaFacebookMessenger, FaInstagram } from 'react-icons/fa';
import { useSiteSettings } from '../context/SiteSettingsContext';
import './ChatIcons.css';

function ChatIcons() {
  const { settings } = useSiteSettings();

  const whatsappNumber = settings.whatsapp_number || settings.contact_phone;
  const messengerUrl = settings.messenger_url;
  const instagramUrl = settings.instagram_url;

  const whatsappLink = whatsappNumber
    ? `https://wa.me/${whatsappNumber.replace(/[^0-9]/g, '')}`
    : null;
  const messengerLink = messengerUrl || null;
  const instagramLink = instagramUrl || null;

  if (!whatsappLink && !messengerLink && !instagramLink) {
    return null;
  }

  return (
    <div className="chat-icons">
      {instagramLink && (
        <a
          href={instagramLink}
          target="_blank"
          rel="noopener noreferrer"
          className="chat-icon chat-icon-instagram"
          aria-label="View on Instagram"
        >
          <FaInstagram />
        </a>
      )}
      {whatsappLink && (
        <a
          href={whatsappLink}
          target="_blank"
          rel="noopener noreferrer"
          className="chat-icon chat-icon-whatsapp"
          aria-label="Chat on WhatsApp"
        >
          <FaWhatsapp />
        </a>
      )}
      {messengerLink && (
        <a
          href={messengerLink}
          target="_blank"
          rel="noopener noreferrer"
          className="chat-icon chat-icon-messenger"
          aria-label="Chat on Messenger"
        >
          <FaFacebookMessenger />
        </a>
      )}
    </div>
  );
}

export default ChatIcons;
