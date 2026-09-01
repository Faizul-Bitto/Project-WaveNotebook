import { useEffect } from 'react';
import { useSiteSettings } from '../context/SiteSettingsContext';
import { withVersion } from '../utils/media';

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
  const { settings, loading } = useSiteSettings();

  // Skip while loading: writing the default seed values first would make the
  // title/favicon flip from default → actual (flash of default content).
  useEffect(() => {
    if (loading) return;
    const title = settings.page_title || settings.site_name;
    if (title) {
      document.title = title;
    }
  }, [loading, settings.page_title, settings.site_name]);

  useEffect(() => {
    if (loading) return;
    if (settings.favicon_url) {
      setFavicon(withVersion(settings.favicon_url, settings.updated_at));
    }
  }, [loading, settings.favicon_url, settings.updated_at]);

  return null;
}

export default SiteMeta;
