import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { getSiteSettings } from '../api/services';

const SiteSettingsContext = createContext();

export const useSiteSettings = () => useContext(SiteSettingsContext);

// Final fallback — only ever RENDERED after the settings request has settled
// (i.e. the API is truly unreachable / returned nothing), never during loading.
const DEFAULT_SETTINGS = {
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
};

export function SiteSettingsProvider({ children }) {
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  // `loading` is true until the settings request settles (success OR failure).
  // Consumers use it to render skeletons instead of default/fallback values,
  // so actual data never replaces visible defaults (no flash of default content).
  const [loading, setLoading] = useState(true);

  // NOTE: `loading` is only for the INITIAL load (and bfcache restores never
  // toggle it, they swap data in place). Silent re-fetches (e.g. after the
  // admin saves settings) must not flash skeletons across the whole site.
  const refresh = useCallback(async () => {
    try {
      const data = await getSiteSettings();
      setSettings(data.settings || DEFAULT_SETTINGS);
    } catch (err) {
      console.error('Failed to load site settings:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

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
    <SiteSettingsContext.Provider value={{ settings, loading, refresh }}>
      {children}
    </SiteSettingsContext.Provider>
  );
}

export default SiteSettingsContext;