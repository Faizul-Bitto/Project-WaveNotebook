import { useEffect, useState } from 'react';
import { FaTrash, FaSearch } from 'react-icons/fa';
import {
  adminGetUsers,
  adminDeleteUser,
} from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';
import Modal from '../../components/Modal';

function AdminUsers() {
  const { addToast } = useToast();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [deleteModal, setDeleteModal] = useState({ show: false, id: null, phone: '' });

  const loadUsers = async (searchTerm = '') => {
    try {
      setLoading(true);
      const params = { limit: 100 };
      if (searchTerm) params.search = searchTerm;
      const data = await adminGetUsers(params);
      setUsers(data.users || []);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to load users.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await adminGetUsers({ limit: 100 });
        if (mounted) setUsers(data.users || []);
      } catch (err) {
        if (mounted) addToast(err.response?.data?.detail || 'Failed to load users.', 'error');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchData();
    return () => {
      mounted = false;
    };
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    await loadUsers(search.trim());
  };

  const handleDelete = async (user) => {
    setDeleteModal({ show: true, id: user.id, phone: user.phone_number });
  };

  const confirmDelete = async () => {
    const { id } = deleteModal;
    setDeleteModal({ show: false, id: null, phone: '' });
    try {
      await adminDeleteUser(id);
      await loadUsers(search);
      addToast('User deleted successfully!', 'success');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to delete user.', 'error');
    }
  };

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h2>Users</h2>
        <form className="admin-search" onSubmit={handleSearch}>
          <input
            type="text"
            placeholder="Search by phone, name, or address..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="submit" className="btn btn-primary">
            <FaSearch />
          </button>
        </form>
      </div>

      {loading ? (
        <div className="loading">Loading users...</div>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Phone</th>
                <th>Email</th>
                <th>Role</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan="6" className="table-empty">No users found</td>
                </tr>
              ) : (
                users.map((user, index) => (
                  <tr key={user.id}>
                    <td>{index + 1}</td>
                    <td>{user.phone_number}</td>
                    <td>{user.email || '-'}</td>
                    <td>
                      <span className={`badge ${user.role === 'admin' ? 'badge-blue' : 'badge-green'}`}>
                        {user.role}
                      </span>
                    </td>
                    <td>{new Date(user.created_at).toLocaleDateString()}</td>
                    <td>
                      <div className="table-actions">
                        {user.role !== 'admin' && (
                          <button
                            className="action-btn action-delete"
                            onClick={() => handleDelete(user)}
                            aria-label={`Delete user ${user.phone_number}`}
                          >
                            <FaTrash />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        isOpen={deleteModal.show}
        onClose={() => setDeleteModal({ show: false, id: null, phone: '' })}
        onConfirm={confirmDelete}
        title="Delete User"
        message={`Are you sure you want to delete user ${deleteModal.phone}? This will delete their orders too.`}
        confirmText="Delete"
        type="danger"
      />
    </div>
  );
}

export default AdminUsers;