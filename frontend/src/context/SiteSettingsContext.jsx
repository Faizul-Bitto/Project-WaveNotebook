import { createContext, useContext, useEffect, useState } from 'react';
import { getSiteSettings } from '../api/services';

const SiteSettingsContext = createContext();

export const useSiteSettings = () => useContext(SiteSettingsContext);

export function SiteSettingsProvider({ children }) {
  const [settings, setSettings] = useState({ logo_url: null, site_name: 'WaveNotebook' });

  const refresh = async () => {
    try {
      const data = await getSiteSettings();
      setSettings(data.settings || { logo_url: null, site_name: 'WaveNotebook' });
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