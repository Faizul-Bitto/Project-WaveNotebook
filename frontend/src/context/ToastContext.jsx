import { createContext, useContext, useCallback } from 'react';
import { GooeyToaster, gooeyToast } from 'goey-toast';
import 'goey-toast/styles.css';

const ToastContext = createContext();

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

export function ToastProvider({ children }) {
  /**
   * Drop-in replacement for the legacy toaster.
   * Same signature: addToast(message, type, duration) -> id
   */
  const addToast = useCallback((message, type = 'info', duration = 3000) => {
    const text = String(message ?? '');
    const options = {
      preset: 'snappy',
      timing: { displayDuration: duration },
      showProgress: duration >= 4000,
    };

    switch (type) {
      case 'success':
        return gooeyToast.success(text, options);
      case 'error':
        return gooeyToast.error(text, options);
      case 'warning':
        return gooeyToast.warning(text, options);
      default:
        return gooeyToast.info(text, options);
    }
  }, []);

  /**
   * Morphing promise toast: pill (loading) -> blob (success / error).
   * Messages may be strings or functions:
   *   toastPromise(uploadFile(file), {
   *     loading: 'Uploading image...',
   *     success: 'Image uploaded!',
   *     error: (err) => err?.response?.data?.detail || 'Upload failed',
   *   })
   */
  const toastPromise = useCallback((promise, messages = {}, options = {}) => {
    return gooeyToast.promise(promise, {
      preset: 'snappy',
      ...options,
      loading: messages.loading || 'Processing...',
      success: messages.success || 'Done successfully!',
      error: messages.error || 'Something went wrong. Please try again.',
    });
  }, []);

  const removeToast = useCallback((id) => {
    gooeyToast.dismiss(id);
  }, []);

  return (
    <ToastContext.Provider value={{ addToast, removeToast, toastPromise, gooeyToast }}>
      <GooeyToaster
        position="top-right"
        theme="dark"
        preset="snappy"
        showTimestamp={true}
      />
      {children}
    </ToastContext.Provider>
  );
}
