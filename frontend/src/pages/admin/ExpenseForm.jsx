import { useEffect, useState } from 'react';
import {
  adminCreateExpense,
  adminUpdateExpense,
  adminGetExpenseDropdowns,
} from '../../api/adminServices';
import { useToast } from '../../context/ToastContext';

const PAYMENT_STATUS_OPTIONS = [
  { value: 'paid', label: 'Paid' },
  { value: 'due', label: 'Due' },
];

function ExpenseForm({ show, onClose, expense, onSuccess }) {
  const { addToast } = useToast();
  const [formData, setFormData] = useState({
    date: '',
    items: '',
    description: '',
    amount: '',
    expense_type_id: '',
    payment_by_id: '',
    payment_method_id: '',
    payment_status: 'paid',
  });
  const [dropdowns, setDropdowns] = useState({ expense_types: [], payment_by: [], payment_methods: [] });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
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
    if (show) loadDropdowns();
  }, [show]);

  useEffect(() => {
    if (expense) {
      setFormData({
        date: expense.date || '',
        items: expense.items || '',
        description: expense.description || '',
        amount: expense.amount || '',
        expense_type_id: expense.expense_type_id || '',
        payment_by_id: expense.payment_by_id || '',
        payment_method_id: expense.payment_method_id || '',
        payment_status: expense.payment_status || 'paid',
      });
    } else {
      setFormData({
        date: new Date().toISOString().split('T')[0],
        items: '',
        description: '',
        amount: '',
        expense_type_id: '',
        payment_by_id: '',
        payment_method_id: '',
        payment_status: 'paid',
      });
    }
  }, [expense]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        ...formData,
        expense_type_id: formData.expense_type_id ? parseInt(formData.expense_type_id) : null,
        payment_by_id: formData.payment_by_id ? parseInt(formData.payment_by_id) : null,
        payment_method_id: formData.payment_method_id ? parseInt(formData.payment_method_id) : null,
        amount: parseFloat(formData.amount),
      };

      if (expense) {
        await adminUpdateExpense(expense.id, payload);
        addToast('Expense updated successfully!', 'success');
      } else {
        await adminCreateExpense(payload);
        addToast('Expense created successfully!', 'success');
      }
      onSuccess();
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to save expense.', 'error');
    } finally {
      setSaving(false);
    }
  };

  if (!show) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{expense ? 'Edit Expense' : 'Add Expense'}</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-row">
              <div className="form-group">
                <label>Date *</label>
                <input
                  type="date"
                  name="date"
                  value={formData.date}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="form-group">
                <label>Amount (৳) *</label>
                <input
                  type="number"
                  name="amount"
                  value={formData.amount}
                  onChange={handleChange}
                  step="0.01"
                  min="0"
                  placeholder="0.00"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label>Items *</label>
              <input
                type="text"
                name="items"
                value={formData.items}
                onChange={handleChange}
                placeholder="e.g., Office supplies, A4 paper"
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Expense Type</label>
                <select name="expense_type_id" value={formData.expense_type_id} onChange={handleChange}>
                  <option value="">Select Type</option>
                  {dropdowns.expense_types.map((t) => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Payment By</label>
                <select name="payment_by_id" value={formData.payment_by_id} onChange={handleChange}>
                  <option value="">Select Person</option>
                  {dropdowns.payment_by.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Payment Method</label>
                <select name="payment_method_id" value={formData.payment_method_id} onChange={handleChange}>
                  <option value="">Select Method</option>
                  {dropdowns.payment_methods.map((m) => (
                    <option key={m.id} value={m.id}>{m.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Payment Status</label>
                <select name="payment_status" value={formData.payment_status} onChange={handleChange}>
                  {PAYMENT_STATUS_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>Description</label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows="3"
                placeholder="Additional details"
              />
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving...' : (expense ? 'Update Expense' : 'Create Expense')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ExpenseForm;
