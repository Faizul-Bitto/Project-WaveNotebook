import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { FaPlus, FaEdit, FaTrash, FaMoneyBillWave, FaMoneyCheck } from 'react-icons/fa';
import {
  adminGetExpenses,
  adminDeleteExpense,
  adminGetExpenseSummary,
  adminGetExpenseDropdowns,
} from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';
import Modal from '../../components/Modal';
import Pagination from '../../components/Pagination';

import ExpenseForm from './ExpenseForm';

const PAGE_SIZE = 20;

const PAYMENT_STATUS_LABELS = {
  paid: 'Paid',
  due: 'Due',
};

function ExpenseDashboard() {
  const navigate = useNavigate();
  const location = useLocation();
  const { addToast } = useToast();
  const [expenses, setExpenses] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingExpense, setEditingExpense] = useState(null);
  const [deleteModal, setDeleteModal] = useState({ show: false, id: null, items: '' });
  const [dropdowns, setDropdowns] = useState({ expense_types: [], payment_by: [], payment_methods: [] });
  const [summary, setSummary] = useState(null);
  const [summaryPeriod, setSummaryPeriod] = useState('all');
  const [summaryYear, setSummaryYear] = useState(new Date().getFullYear());
  const [summaryMonth, setSummaryMonth] = useState(new Date().getMonth() + 1);
  const [summaryDate, setSummaryDate] = useState(new Date().toISOString().slice(0, 10));
  const [paymentStatusFilter, setPaymentStatusFilter] = useState('');

  const loadDropdowns = async () => {
    try {
      const data = await adminGetExpenseDropdowns();
      setDropdowns({
        expense_types: data.expense_types || [],
        payment_by: data.payment_by || [],
        payment_methods: data.payment_methods || [],
      });
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to load dropdown data.', 'error');
    }
  };

  const loadExpenses = async (status = paymentStatusFilter, pageNum = page, period = summaryPeriod, yr = summaryYear, mo = summaryMonth, dt = summaryDate) => {
    try {
      setLoading(true);
      const params = {
        skip: pageNum * PAGE_SIZE,
        limit: PAGE_SIZE,
      };
      if (status) params.status = status;
      if (period !== 'all') {
        params.period = period;
        if (period === 'year') params.year = yr;
        if (period === 'month') { params.year = yr; params.month = mo; }
        if (period === 'day') params.date = dt;
      }
      const data = await adminGetExpenses(params);
      setExpenses(data.expenses || []);
      setTotal(data.total || 0);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to load expenses.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadSummary = async () => {
    try {
      const params = { period: summaryPeriod };
      if (summaryPeriod === 'year') params.year = summaryYear;
      if (summaryPeriod === 'month') {
        params.year = summaryYear;
        params.month = summaryMonth;
      }
      if (summaryPeriod === 'day') params.date = summaryDate;
      const data = await adminGetExpenseSummary(params);
      setSummary(data);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to load summary.', 'error');
    }
  };

  useEffect(() => {
    loadDropdowns();
    const params = new URLSearchParams(location.search);
    const initialStatus = params.get('status') || '';
    setPaymentStatusFilter(initialStatus);
    loadExpenses(initialStatus, 0);
  }, []);

  const handlePaymentStatusChange = (e) => {
    const value = e.target.value;
    setPaymentStatusFilter(value);
    setPage(0);
    navigate({ pathname: '/admin/expenses', search: value ? `?status=${value}` : '' }, { replace: true });
    loadExpenses(value, 0);
  };

  const handlePageChange = (newPage) => {
    setPage(newPage);
    loadExpenses(paymentStatusFilter, newPage);
  };

  useEffect(() => {
    loadSummary();
  }, [summaryPeriod, summaryYear, summaryMonth, summaryDate]);

  const handleSummaryPeriodChange = (e) => {
    const value = e.target.value;
    setSummaryPeriod(value);
    setPage(0);
    loadExpenses(paymentStatusFilter, 0, value, summaryYear, summaryMonth, summaryDate);
  };

  const handleSummaryYearChange = (e) => {
    const value = parseInt(e.target.value);
    setSummaryYear(value);
    setPage(0);
    loadExpenses(paymentStatusFilter, 0, summaryPeriod, value, summaryMonth, summaryDate);
  };

  const handleSummaryMonthChange = (e) => {
    const value = parseInt(e.target.value);
    setSummaryMonth(value);
    setPage(0);
    loadExpenses(paymentStatusFilter, 0, summaryPeriod, summaryYear, value, summaryDate);
  };

  const handleSummaryDateChange = (e) => {
    const value = e.target.value;
    setSummaryDate(value);
    setPage(0);
    loadExpenses(paymentStatusFilter, 0, summaryPeriod, summaryYear, summaryMonth, value);
  };

  const handleEdit = (expense) => {
    setEditingExpense(expense);
    setShowForm(true);
  };

  const handleDelete = (expense) => {
    setDeleteModal({ show: true, id: expense.id, items: expense.items });
  };

  const confirmDelete = async () => {
    const { id } = deleteModal;
    setDeleteModal({ show: false, id: null, items: '' });
    try {
      await adminDeleteExpense(id);
      addToast('Expense deleted successfully!', 'success');
      setPage(0);
      loadExpenses(paymentStatusFilter, 0);
      loadSummary();
      window.dispatchEvent(new CustomEvent('expense-updated'));
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to delete expense.', 'error');
    }
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setEditingExpense(null);
    loadExpenses(paymentStatusFilter, page);
    loadSummary();
    window.dispatchEvent(new CustomEvent('expense-updated'));
  };

  const availableYears = [];
  const currentYear = new Date().getFullYear();
  for (let y = currentYear - 5; y <= currentYear; y++) availableYears.push(y);
  const months = Array.from({ length: 12 }, (_, i) => i + 1);

  return (
    <div className="admin-page">
      <div className="admin-page-header">
        <h2>Expenses</h2>
        <button className="btn btn-primary" onClick={() => { setEditingExpense(null); setShowForm(true); }}>
          <FaPlus /> Add Expense
        </button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="stats-grid" style={{ marginBottom: '24px' }}>
          <div className="stat-card stat-blue">
            <div className="stat-icon"><FaMoneyBillWave /></div>
            <div className="stat-info">
              <span className="stat-value">৳{summary.total_expense?.toLocaleString()}</span>
              <span className="stat-label">Total Expense</span>
            </div>
          </div>
          <div className="stat-card stat-green">
            <div className="stat-icon"><FaMoneyCheck /></div>
            <div className="stat-info">
              <span className="stat-value">৳{summary.total_paid?.toLocaleString()}</span>
              <span className="stat-label">Paid</span>
            </div>
          </div>
          <div className="stat-card stat-orange">
            <div className="stat-icon"><FaMoneyCheck /></div>
            <div className="stat-info">
              <span className="stat-value">৳{summary.total_due?.toLocaleString()}</span>
              <span className="stat-label">Due</span>
            </div>
          </div>
        </div>
      )}

      {/* Summary Filters */}
      <div className="admin-filters">
        <div className="admin-filters-group">
        <select value={paymentStatusFilter} onChange={handlePaymentStatusChange}>
          <option value="">All Payments</option>
          <option value="paid">Paid</option>
          <option value="due">Due</option>
        </select>
        <select value={summaryPeriod} onChange={handleSummaryPeriodChange}>
          <option value="all">All Time</option>
          <option value="year">Year</option>
          <option value="month">Month</option>
          <option value="week">Week</option>
          <option value="day">Date</option>
        </select>
        {summaryPeriod === 'year' && (
          <select value={summaryYear} onChange={handleSummaryYearChange}>
            {availableYears.map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        )}
        {summaryPeriod === 'month' && (
          <>
            <select value={summaryYear} onChange={handleSummaryYearChange}>
              {availableYears.map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
            <select value={summaryMonth} onChange={handleSummaryMonthChange}>
              {months.map((m) => (
                <option key={m} value={m}>
                  {new Date(2000, m - 1, 1).toLocaleString('default', { month: 'long' })}
                </option>
              ))}
            </select>
          </>
        )}
        {summaryPeriod === 'day' && (
          <input
            type="date"
            value={summaryDate}
            max={new Date().toISOString().slice(0, 10)}
            onChange={handleSummaryDateChange}
          />
        )}
        </div>
      </div>

      {/* Expenses Table */}
      {loading ? (
        <div className="loading">Loading expenses...</div>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Date</th>
                <th>Items</th>
                <th>Expense Type</th>
                <th>Payment By</th>
                <th>Payment Method</th>
                <th>Amount (৳)</th>
                <th>Payment Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {expenses.length === 0 ? (
                <tr><td colSpan="9" className="table-empty">No expenses found</td></tr>
              ) : (
                expenses.map((expense, index) => (
                  <tr key={expense.id}>
                    <td>{page * PAGE_SIZE + index + 1}</td>
                    <td>{expense.date}</td>
                    <td>{expense.items}</td>
                    <td>{expense.expense_type_name || '—'}</td>
                    <td>{expense.payment_by_name || '—'}</td>
                    <td>{expense.payment_method_name || '—'}</td>
                    <td>{parseFloat(expense.amount).toLocaleString()}</td>
                    <td>
                      <span className={`badge ${expense.payment_status === 'paid' ? 'badge-green' : 'badge-orange'}`}>
                        {PAYMENT_STATUS_LABELS[expense.payment_status] || expense.payment_status}
                      </span>
                    </td>
                    <td>
                      <div className="table-actions">
                        <button
                          className="action-btn action-edit"
                          onClick={() => handleEdit(expense)}
                          aria-label={`Edit expense ${expense.id}`}
                        >
                          <FaEdit />
                        </button>
                        <button
                          className="action-btn action-delete"
                          onClick={() => handleDelete(expense)}
                          aria-label={`Delete expense ${expense.id}`}
                        >
                          <FaTrash />
                        </button>
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

      <ExpenseForm
        show={showForm}
        onClose={() => { setShowForm(false); setEditingExpense(null); }}
        expense={editingExpense}
        dropdowns={dropdowns}
        onSuccess={handleFormSuccess}
      />

      <Modal
        isOpen={deleteModal.show}
        onClose={() => setDeleteModal({ show: false, id: null, items: '' })}
        onConfirm={confirmDelete}
        title="Delete Expense"
        message={`Are you sure you want to delete expense "${deleteModal.items}"?`}
        confirmText="Delete"
        type="danger"
      />
    </div>
  );
}

export default ExpenseDashboard;
