import { useEffect, useState } from 'react';
import { FaTrash, FaSearch, FaFileExcel, FaFileCsv } from 'react-icons/fa';
import {
  adminGetUsers,
  adminDeleteUser,
  adminExportUsers,
} from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';
import Modal from '../../components/Modal';
import Pagination from '../../components/Pagination';

const PAGE_SIZE = 20;

function AdminUsers() {
  const { addToast } = useToast();
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [activeSearch, setActiveSearch] = useState('');
  const [deleteModal, setDeleteModal] = useState({ show: false, id: null, phone: '' });

  const loadUsers = async (searchTerm = activeSearch, pageNum = page) => {
    try {
      setLoading(true);
      const params = {
        skip: pageNum * PAGE_SIZE,
        limit: PAGE_SIZE,
      };
      if (searchTerm) params.search = searchTerm;
      const data = await adminGetUsers(params);
      setUsers(data.users || []);
      setTotal(data.total || 0);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to load users.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers('', 0);
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    const term = search.trim();
    setActiveSearch(term);
    setPage(0);
    loadUsers(term, 0);
  };

  const handleClearSearch = () => {
    setSearch('');
    setActiveSearch('');
    setPage(0);
    loadUsers('', 0);
  };

  const handlePageChange = (newPage) => {
    setPage(newPage);
    loadUsers(activeSearch, newPage);
  };

  const handleExport = async (suffix) => {
    try {
      const filename = await adminExportUsers(
        activeSearch ? { search: activeSearch } : {},
        suffix
      );
      addToast(`${filename} downloaded!`, 'success');
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to export users.', 'error');
    }
  };

  const handleDelete = async (user) => {
    setDeleteModal({ show: true, id: user.id, phone: user.phone_number });
  };

  const confirmDelete = async () => {
    const { id } = deleteModal;
    setDeleteModal({ show: false, id: null, phone: '' });
    try {
      await adminDeleteUser(id);
      setPage(0);
      await loadUsers(activeSearch, 0);
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
          {activeSearch && (
            <button type="button" className="btn btn-secondary btn-sm" onClick={handleClearSearch}>
              Clear
            </button>
          )}
        </form>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={() => handleExport('xlsx')} title="Export users to Excel">
            <FaFileExcel /> Excel
          </button>
          <button className="btn btn-secondary" onClick={() => handleExport('csv')} title="Export users to CSV">
            <FaFileCsv /> CSV
          </button>
        </div>
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
                    <td>{page * PAGE_SIZE + index + 1}</td>
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

      {/* Pagination */}
      {!loading && (
        <Pagination
          page={page}
          total={total}
          pageSize={PAGE_SIZE}
          onPageChange={handlePageChange}
          loading={loading}
        />
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