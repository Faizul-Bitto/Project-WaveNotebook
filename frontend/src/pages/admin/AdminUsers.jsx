import { useEffect, useState } from 'react';
import { FaTrash, FaSearch } from 'react-icons/fa';
import {
  adminGetUsers,
  adminDeleteUser,
} from '../../api/adminServices';

function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');

  const loadUsers = async (searchTerm = '') => {
    try {
      setLoading(true);
      const params = { limit: 100 };
      if (searchTerm) params.search = searchTerm;
      const data = await adminGetUsers(params);
      setUsers(data.users || []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load users.');
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
        if (mounted) setError(null);
      } catch (err) {
        if (mounted) setError(err.response?.data?.detail || 'Failed to load users.');
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
    if (window.confirm(`Are you sure you want to delete user ${user.phone_number}? This will delete their orders too.`)) {
      try {
        await adminDeleteUser(user.id);
        await loadUsers(search);
      } catch (err) {
        alert(err.response?.data?.detail || 'Failed to delete user.');
      }
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

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="loading">Loading users...</div>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
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
                users.map((user) => (
                  <tr key={user.id}>
                    <td>{user.id}</td>
                    <td>{user.phone_number}</td>
                    <td>{user.email || '-'}</td>
                    <td>
                      <span className={`badge ${user.role === 'admin' ? 'badge-blue' : 'badge-green'}`}>
                        {user.role}
                      </span>
                    </td>
                    <td>{new Date(user.created_at).toLocaleDateString()}</td>
                    <td className="table-actions">
                      {user.role !== 'admin' && (
                        <button
                          className="action-btn action-delete"
                          onClick={() => handleDelete(user)}
                          aria-label={`Delete user ${user.phone_number}`}
                        >
                          <FaTrash />
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default AdminUsers;