import { createContext, useContext, useEffect, useState } from 'react';
import { getSiteSettings } from '../api/services';

const SiteSettingsContext = createContext();

export const useSiteSettings = () => useContext(SiteSettingsContext);

export function SiteSettingsProvider({ children }) {
  const [settings, setSettings] = useState({
    logo_url: null,
    favicon_url: null,
    updated_at: null,
    site_name: 'WaveNotebook',
    page_title: null,
    site_description: null,
    contact_phone: null,
    contact_email: null,
    contact_address: null,
    hotline_number: null,
    website_url: null,
    facebook_url: null,
    youtube_url: null,
    instagram_url: null,
    twitter_url: null,
    whatsapp_number: null,
    messenger_url: null,
    order_whatsapp_number: null,
    order_call_number: null,
    privacy_policy: null,
    terms_conditions: null,
    refund_policy: null,
  });

  const refresh = async () => {
    try {
      const data = await getSiteSettings();
      setSettings(data.settings || {
        logo_url: null,
        favicon_url: null,
        updated_at: null,
        site_name: 'WaveNotebook',
        page_title: null,
        site_description: null,
        contact_phone: null,
        contact_email: null,
        contact_address: null,
        hotline_number: null,
        website_url: null,
        facebook_url: null,
        youtube_url: null,
        instagram_url: null,
        twitter_url: null,
        whatsapp_number: null,
        messenger_url: null,
        order_whatsapp_number: null,
        order_call_number: null,
        privacy_policy: null,
        terms_conditions: null,
        refund_policy: null,
      });
    } catch (err) {
      console.error('Failed to load site settings:', err);
    }
  };

  useEffect(() => { refresh(); }, []);

  // When the browser restores this page from the back/forward cache (bfcache),
  // it shows the OLD render instantly — which is exactly the "previous
  // logo/banner flashes first" behaviour. Re-fetch settings so the UI updates.
  useEffect(() => {
    const onPageShow = (event) => {
      if (event.persisted) refresh();
    };
    window.addEventListener('pageshow', onPageShow);
    return () => window.removeEventListener('pageshow', onPageShow);
  }, []);

  return (
    <SiteSettingsContext.Provider value={{ settings, refresh }}>
      {children}
    </SiteSettingsContext.Provider>
  );
}

export default SiteSettingsContext;