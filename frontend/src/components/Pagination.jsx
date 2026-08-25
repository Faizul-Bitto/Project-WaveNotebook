function Pagination({ page = 0, total = 0, pageSize = 20, onPageChange, loading = false }) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const from = total === 0 ? 0 : page * pageSize + 1;
  const to = Math.min((page + 1) * pageSize, total);

  const handlePrev = () => {
    if (page > 0 && !loading && onPageChange) {
      onPageChange(page - 1);
    }
  };

  const handleNext = () => {
    if (page + 1 < totalPages && !loading && onPageChange) {
      onPageChange(page + 1);
    }
  };

  const infoText = total === 0
    ? 'Showing 0 of 0'
    : from === to
      ? `Showing ${from} of ${total}`
      : `Showing ${from} - ${to} of ${total}`;

  return (
    <div className="admin-pagination">
      <div className="admin-pagination-info">
        {infoText}
      </div>
      <div className="admin-pagination-controls">
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={handlePrev}
          disabled={page === 0 || loading}
          aria-label="Previous page"
        >
          Previous
        </button>
        <span className="admin-page-info">
          Page {page + 1} of {totalPages}
        </span>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={handleNext}
          disabled={page + 1 >= totalPages || loading}
          aria-label="Next page"
        >
          Next
        </button>
      </div>
    </div>
  );
}

export default Pagination;
