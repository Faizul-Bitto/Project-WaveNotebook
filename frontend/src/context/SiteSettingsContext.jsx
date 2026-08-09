import { createContext, useContext, useEffect, useState } from 'react';
import { getSiteSettings } from '../api/services';

const SiteSettingsContext = createContext();

export const useSiteSettings = () => useContext(SiteSettingsContext);

export function SiteSettingsProvider({ children }) {
  const [settings, setSettings] = useState({
    logo_url: null,
    site_name: 'WaveNotebook',
    site_description: null,
    contact_phone: null,
    contact_email: null,
    contact_address: null,
    hotline_number: null,
    facebook_url: null,
    youtube_url: null,
    instagram_url: null,
    twitter_url: null,
    whatsapp_number: null,
    messenger_url: null,
    privacy_policy: null,
    terms_conditions: null,
    refund_policy: null,
  });

  const refresh = async () => {
    try {
      const data = await getSiteSettings();
      setSettings(data.settings || {
        logo_url: null,
        site_name: 'WaveNotebook',
        site_description: null,
        contact_phone: null,
        contact_email: null,
        contact_address: null,
        hotline_number: null,
        facebook_url: null,
        youtube_url: null,
        instagram_url: null,
        twitter_url: null,
        whatsapp_number: null,
        messenger_url: null,
        privacy_policy: null,
        terms_conditions: null,
        refund_policy: null,
      });
    } catch (err) {
      console.error('Failed to load site settings:', err);
    }
  };

  useEffect(() => { refresh(); }, []);

  return (
    <SiteSettingsContext.Provider value={{ settings, refresh }}>
      {children}
    </SiteSettingsContext.Provider>
  );
}

export default SiteSettingsContext;