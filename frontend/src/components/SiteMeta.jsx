import { useEffect } from 'react';
import { useSiteSettings } from '../context/SiteSettingsContext';

function setFavicon(url) {
  document.querySelectorAll('link[rel*="icon"]').forEach((link) => {
    link.parentNode.removeChild(link);
  });
  const link = document.createElement('link');
  link.rel = 'icon';
  link.href = url;
  document.head.appendChild(link);
}

function SiteMeta() {
  const { settings } = useSiteSettings();

  useEffect(() => {
    const title = settings.page_title || settings.site_name;
    if (title) {
      document.title = title;
    }
  }, [settings.page_title, settings.site_name]);

  useEffect(() => {
    if (settings.favicon_url) {
      setFavicon(settings.favicon_url);
    }
  }, [settings.favicon_url]);

  return null;
}

export default SiteMeta;
