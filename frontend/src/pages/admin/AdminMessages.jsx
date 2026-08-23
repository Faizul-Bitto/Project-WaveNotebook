import { useCallback, useEffect, useState } from 'react';
import { FaEnvelopeOpenText, FaTrash, FaEye, FaCircle } from 'react-icons/fa';
import {
  adminGetContacts,
  adminMarkMessageRead,
  adminDeleteMessage,
} from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';
import Modal from '../../components/Modal';

function AdminMessages() {
  const { addToast } = useToast();
  const [messages, setMessages] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [viewMessage, setViewMessage] = useState(null);
  const [deleteModal, setDeleteModal] = useState({ show: false, id: null, name: '' });

  const loadMessages = useCallback(
    async (currentFilter = filter) => {
      try {
        setLoading(true);
        const data = await adminGetContacts({ filter: currentFilter, limit: 100 });
        setMessages(data.messages || []);
        setTotal(data.total || 0);
      } catch (err) {
        addToast(err.response?.data?.detail || 'Failed to load messages.', 'error');
      } finally {
        setLoading(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [filter]
  );

  useEffect(() => {
    loadMessages(filter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  // Light polling so newly sent messages appear without manual refresh
  useEffect(() => {
    const interval = setInterval(() => {
      loadMessages(filter);
    }, 20000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const handleView = async (message) => {
    setViewMessage(message);
    if (!message.is_read) {
      try {
        await adminMarkMessageRead(message.id);
        setMessages((prev) =>
          prev.map((m) => (m.id === message.id ? { ...m, is_read: true } : m))
        );
        window.dispatchEvent(new CustomEvent('contact-message-read'));
      } catch {
        // non-blocking - viewing still works
      }
    }
  };

  const handleDeleteClick = (message) => {
    setDeleteModal({ show: true, id: message.id, name: message.name });
  };

  const confirmDelete = async () => {
    try {
      await adminDeleteMessage(deleteModal.id);
      addToast('Message deleted successfully.', 'success');
      setViewMessage(null);
      loadMessages(filter);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to delete message.', 'error');
    } finally {
      setDeleteModal({ show: false, id: null, name: '' });
    }
  };

  const formatDate = (iso) => {
    if (!iso) return '-';
    const d = new Date(iso);
    return d.toLocaleString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const unreadCount = messages.filter((m) => !m.is_read).length;

  return (
    <div className="admin-page messages-page">
      {/* Header */}
      <div className="admin-page-header">
        <div>
          <h1>Contact Messages</h1>
          <p className="admin-page-info">
            {total} message{total !== 1 ? 's' : ''} total
            {unreadCount > 0 ? ` • ${unreadCount} unread` : ''}
          </p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="messages-filter-tabs">
        {[
          { key: 'all', label: 'All' },
          { key: 'unread', label: 'Unread' },
          { key: 'read', label: 'Read' },
        ].map((tab) => (
          <button
            key={tab.key}
            className={`messages-tab ${filter === tab.key ? 'active' : ''}`}
            onClick={() => setFilter(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Messages List */}
      {loading ? (
        <div className="loading">Loading messages...</div>
      ) : messages.length === 0 ? (
        <div className="empty-state">
          <FaEnvelopeOpenText style={{ fontSize: 42, marginBottom: 12, opacity: 0.4 }} />
          <h3>No messages</h3>
          <p>Messages sent from the Contact page will appear here.</p>
        </div>
      ) : (
        <div className="messages-list">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`message-item ${!m.is_read ? 'unread' : ''}`}
              onClick={() => handleView(m)}
            >
              <div className="message-main">
                <div className="message-top-row">
                  {!m.is_read && <FaCircle className="unread-dot" />}
                  <span className="message-name">{m.name}</span>
                  <span className="message-date">{formatDate(m.created_at)}</span>
                </div>
                <p className="message-preview">
                  {m.message.length > 90 ? `${m.message.slice(0, 90)}...` : m.message}
                </p>
                <div className="message-meta">
                  <a
                    href={`tel:${(m.phone_number || '').replace(/[^+\d]/g, '')}`}
                    onClick={(e) => e.stopPropagation()}
                  >
                    {m.phone_number}
                  </a>
                  {m.email && (
                    <>
                      <span className="meta-sep">•</span>
                      <a
                        href={`mailto:${m.email}`}
                        onClick={(e) => e.stopPropagation()}
                      >
                        {m.email}
                      </a>
                    </>
                  )}
                </div>
              </div>
              <div className="message-actions">
                <button
                  type="button"
                  className="msg-action-btn view"
                  title="View message"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleView(m);
                  }}
                >
                  <FaEye />
                </button>
                <button
                  type="button"
                  className="msg-action-btn delete"
                  title="Delete message"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteClick(m);
                  }}
                >
                  <FaTrash />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* View Message Modal */}
      {viewMessage && (
        <div className="modal-overlay" onClick={() => setViewMessage(null)}>
          <div className="message-view-modal" onClick={(e) => e.stopPropagation()}>
            <div className="message-view-header">
              <h2>Message from {viewMessage.name}</h2>
              <button
                type="button"
                className="message-view-close"
                onClick={() => setViewMessage(null)}
              >
                ✕
              </button>
            </div>
            <div className="message-view-meta">
              <div>
                <span className="meta-label">Phone:</span>{' '}
                <a href={`tel:${(viewMessage.phone_number || '').replace(/[^+\d]/g, '')}`}>
                  {viewMessage.phone_number}
                </a>
              </div>
              <div>
                <span className="meta-label">Email:</span>{' '}
                {viewMessage.email && (
                  <a href={`mailto:${viewMessage.email}`}>{viewMessage.email}</a>
                )}
              </div>
              <div>
                <span className="meta-label">Received:</span>{' '}
                {formatDate(viewMessage.created_at)}
              </div>
            </div>
            <div className="message-view-body">{viewMessage.message}</div>
            <div className="message-view-footer">
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => setViewMessage(null)}
              >
                Close
              </button>
              <button
                type="button"
                className="btn btn-danger"
                onClick={() => handleDeleteClick(viewMessage)}
              >
                <FaTrash /> Delete
              </button>
            </div>
          </div>
        </div>
      )}

      <Modal
        isOpen={deleteModal.show}
        onClose={() => setDeleteModal({ show: false, id: null, name: '' })}
        onConfirm={confirmDelete}
        title="Delete Message"
        message={`Are you sure you want to delete the message from ${deleteModal.name}?`}
        confirmText="Delete"
        type="danger"
      />
    </div>
  );
}

export default AdminMessages;