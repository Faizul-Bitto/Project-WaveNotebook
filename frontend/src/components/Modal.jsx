import { FaTimes, FaExclamationTriangle } from 'react-icons/fa';

function Modal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  type = 'warning',
}) {
  if (!isOpen) return null;

  const icon = {
    warning: <FaExclamationTriangle className="modal-icon modal-icon-warning" />,
    danger: <FaExclamationTriangle className="modal-icon modal-icon-danger" />,
    info: null,
  }[type] || null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-confirm" onClick={(e) => e.stopPropagation()}>
        <div className="modal-confirm-header">
          {icon}
          <h3 className="modal-confirm-title">{title}</h3>
          <button className="modal-confirm-close" onClick={onClose}>
            <FaTimes />
          </button>
        </div>
        <div className="modal-confirm-body">
          <p>{message}</p>
        </div>
        <div className="modal-confirm-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            {cancelText}
          </button>
          <button
            className={`btn ${type === 'danger' ? 'btn-danger' : 'btn-primary'}`}
            onClick={onConfirm}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

export default Modal;
