import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';

export default function TopProgressBar() {
  const location = useLocation();
  const [active, setActive] = useState(false);

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      setActive(true);
      const timer = setTimeout(() => setActive(false), 600);
      return () => clearTimeout(timer);
    });
    return () => cancelAnimationFrame(frame);
  }, [location.pathname]);

  return (
    <div className={`top-progress-bar ${active ? 'active' : ''}`}>
      <div className="top-progress-bar-fill" />
    </div>
  );
}
