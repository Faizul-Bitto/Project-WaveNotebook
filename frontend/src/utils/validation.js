/**
 * Shared form validation used across the application.
 *
 * Usage in a page:
 *   const [errors, setErrors] = useState({});
 *   const errs = validateForm(formData, {
 *     full_name: { label: 'Full name', required: true },
 *     phone_number: { label: 'Phone number', required: true, minLength: 11 },
 *     email: { label: 'Email', pattern: PATTERNS.email, message: 'Enter a valid email.' },
 *   });
 *   if (Object.keys(errs).length) {
 *     setErrors(errs);
 *     return;
 *   }
 *
 * In JSX mark the group invalid and show the message:
 *   <div className={`form-group ${errors.full_name ? 'field-invalid' : ''}`}>
 *     <input ... />
 *     {errors.full_name && <span className="field-error">{errors.full_name}</span>}
 *   </div>
 */

export const PATTERNS = {
  email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  bdPhone: /^01[3-9]\d{8}$/,
  phoneDigits: /^\d{10,14}$/,
  number: /^\d+(\.\d+)?$/,
};

/**
 * Validate `values` against `rules`.
 *
 * SEQUENTIAL MODE: returns ONLY the FIRST failing rule, in field order —
 * e.g. { phone_number: "Please enter a valid phone number." } — so the UI
 * highlights one field at a time and the toast shows exactly that message.
 * Returns an empty object when everything is valid.
 */
export function validateForm(values, rules) {
  const errors = {};

  for (const [field, rule] of Object.entries(rules || {})) {
    const raw = values ? values[field] : undefined;
    const text = raw === null || raw === undefined ? '' : String(raw).trim();
    const label = rule.label || field.replace(/_/g, ' ');

    // Required check
    if (rule.required && !text) {
      errors[field] = rule.requiredMessage || `${capitalize(label)} is required.`;
      return errors;
    }

    // Optional & empty — skip further checks
    if (!text) continue;

    if (rule.minLength && text.length < rule.minLength) {
      errors[field] = `${capitalize(label)} must be at least ${rule.minLength} characters.`;
      return errors;
    }

    if (rule.maxLength && text.length > rule.maxLength) {
      errors[field] = `${capitalize(label)} cannot exceed ${rule.maxLength} characters.`;
      return errors;
    }

    if (rule.min !== undefined && parseFloat(text) < rule.min) {
      errors[field] = `${capitalize(label)} must be at least ${rule.min}.`;
      return errors;
    }

    if (rule.max !== undefined && parseFloat(text) > rule.max) {
      errors[field] = `${capitalize(label)} cannot be more than ${rule.max}.`;
      return errors;
    }

    if (rule.pattern && !rule.pattern.test(text)) {
      errors[field] = rule.message || `${capitalize(label)} format is invalid.`;
      return errors;
    }

    if (typeof rule.custom === 'function') {
      const message = rule.custom(text, values);
      if (message) {
        errors[field] = message;
        return errors;
      }
    }
  }

  return errors;
}

/** Remove one field's error (call from onChange so the highlight clears as the user fixes it). */
export function clearFieldError(errors, field) {
  if (!errors || !errors[field]) return errors;
  const next = { ...errors };
  delete next[field];
  return next;
}

/** First error message — handy for a summary toast. */
export function firstError(errors) {
  if (!errors) return null;
  return Object.values(errors)[0] || null;
}

function capitalize(text) {
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : text;
}