import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

// Centered route-change loader: a sound-wave of vertical bars pulsing in the
// site's price color, floating over a soft translucent blur. No card, no box,
// no text. Clicks pass through and it clears quickly.
export default function PageLoader() {
  const location = useLocation();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const show = requestAnimationFrame(() => setVisible(true));
    const hide = setTimeout(() => setVisible(false), 550);
    return () => {
      cancelAnimationFrame(show);
      clearTimeout(hide);
    };
  }, [location.pathname]);

  return (
    <AnimatePresence>
      { visible && (
        <motion.div
          className="page-loader-overlay"
          initial={ { opacity: 0 } }
          animate={ { opacity: 1 } }
          exit={ { opacity: 0 } }
          transition={ { duration: 0.22, ease: [0.4, 0, 0.2, 1] } }
        >
          <motion.div
            className="loader-bars-wrap"
            initial={ { opacity: 0, scale: 0.6 } }
            animate={ { opacity: 1, scale: 1 } }
            exit={ { opacity: 0, scale: 0.6 } }
            transition={ { duration: 0.25, ease: [0.34, 1.35, 0.64, 1] } }
          >
            <div className="loader-bars" role="status" aria-label="Loading">
              <span className="loader-bar" />
              <span className="loader-bar" />
              <span className="loader-bar" />
              <span className="loader-bar" />
              <span className="loader-bar" />
            </div>
          </motion.div>
        </motion.div>
      ) }
    </AnimatePresence>
  );
}
