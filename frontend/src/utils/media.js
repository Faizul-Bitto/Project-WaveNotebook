// Returns the URL with a version query param derived from the record's
// updated_at timestamp. Whenever an image (banner/logo/favicon) is replaced,
// the URL changes, so browsers can never serve a stale cached copy.
export function withVersion ( url, updatedAt ) {
  if ( !url ) return url;
  const ts = updatedAt ? new Date( updatedAt ).getTime() : 0;
  if ( !ts || Number.isNaN( ts ) ) return url;
  return `${ url }${ url.includes( '?' ) ? '&' : '?' }v=${ ts }`;
}
