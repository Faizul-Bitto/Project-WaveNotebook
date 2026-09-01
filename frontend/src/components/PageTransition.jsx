import { motion } from 'framer-motion';

// Subtle crossfade between routes. The EXIT is intentionally shorter than
// the ENTER: with AnimatePresence mode="wait" the next page cannot mount
// until the current one has left, so a long exit adds dead time and makes
// navigation feel sluggish.
const pageVariants = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: { duration: 0.2, ease: [0.4, 0, 0.2, 1] },
  },
  exit: {
    opacity: 0,
    transition: { duration: 0.12, ease: 'easeIn' },
  },
};

export default function PageTransition({ children }) {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      {children}
    </motion.div>
  );
}
