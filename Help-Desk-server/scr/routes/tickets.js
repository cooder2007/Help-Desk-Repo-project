const express = require('express');
const { body, validationResult } = require('express-validator');
const pool = require('../db/pool');
const auth = require('../middleware/auth');

const router = express.Router();

// Create ticket (student)
router.post(
  '/',
  auth(['student']),
  [
    body('title').isLength({ min: 5 }),
    body('description').isLength({ min: 10 }),
    body('category').isIn(['academics','finance','hostel','it']),
    body('priority').optional().isIn(['low','normal','high','urgent']),
  ],
  async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) return res.status(400).json({ errors: errors.array() });

    const { title, description, category, priority = 'normal' } = req.body;
    const { rows } = await pool.query(
      `INSERT INTO tickets (student_id, title, description, category, priority)
       VALUES ($1,$2,$3,$4,$5) RETURNING *`,
      [req.user.id, title, description, category, priority]
    );
    res.status(201).json(rows[0]);
  }
);

// List tickets (student sees own; staff/admin see all)
router.get('/', auth(['student','staff','admin']), async (req, res) => {
  const role = req.user.role;
  const { status, category } = req.query;

  let base = 'SELECT t.*, u.name AS student_name FROM tickets t JOIN users u ON u.id=t.student_id';
  const params = [];
  const where = [];

  if (role === 'student') {
    where.push('t.student_id=$' + (params.length + 1));
    params.push(req.user.id);
  }
  if (status) {
    where.push('t.status=$' + (params.length + 1));
    params.push(status);
  }
  if (category) {
    where.push('t.category=$' + (params.length + 1));
    params.push(category);
  }

  const sql = where.length ? `${base} WHERE ${where.join(' AND ')} ORDER BY t.created_at DESC`
                           : `${base} ORDER BY t.created_at DESC`;

  const { rows } = await pool.query(sql, params);
  res.json(rows);
});

// Get single ticket + messages
router.get('/:id', auth(['student','staff','admin']), async (req, res) => {
  const ticketId = Number(req.params.id);
  const { rows: trows } = await pool.query('SELECT * FROM tickets WHERE id=$1', [ticketId]);
  const ticket = trows[0];
  if (!ticket) return res.status(404).json({ error: 'Not found' });

  if (req.user.role === 'student' && ticket.student_id !== req.user.id) {
    return res.status(403).json({ error: 'Forbidden' });
  }

  const { rows: mrows } = await pool.query(
    `SELECT tm.*, u.name AS author_name, u.role AS author_role
     FROM ticket_messages tm JOIN users u ON u.id=tm.author_id
     WHERE tm.ticket_id=$1 ORDER BY tm.created_at ASC`,
    [ticketId]
  );

  res.json({ ticket, messages: mrows });
});

// Add message (student or staff)
router.post('/:id/messages', auth(['student','staff','admin']), [body('message').isLength({ min: 2 })], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) return res.status(400).json({ errors: errors.array() });

  const ticketId = Number(req.params.id);
  const { rows: trows } = await pool.query('SELECT * FROM tickets WHERE id=$1', [ticketId]);
  const ticket = trows[0];
  if (!ticket) return res.status(404).json({ error: 'Not found' });

  if (req.user.role === 'student' && ticket.student_id !== req.user.id) {
    return res.status(403).json({ error: 'Forbidden' });
  }

  const { rows } = await pool.query(
    'INSERT INTO ticket_messages (ticket_id, author_id, message) VALUES ($1,$2,$3) RETURNING *',
    [ticketId, req.user.id, req.body.message]
  );

  // Update ticket timestamp
  await pool.query('UPDATE tickets SET updated_at=NOW() WHERE id=$1', [ticketId]);

  res.status(201).json(rows[0]);
});

// Update status (staff/admin)
router.patch('/:id/status', auth(['staff','admin']), [body('status').isIn(['open','in_progress','resolved','closed'])], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) return res.status(400).json({ errors: errors.array() });

  const ticketId = Number(req.params.id);
  const { rows } = await pool.query('UPDATE tickets SET status=$1, updated_at=NOW() WHERE id=$2 RETURNING *', [
    req.body.status,
    ticketId,
  ]);
  if (!rows[0]) return res.status(404).json({ error: 'Not found' });
  res.json(rows[0]);
});

module.exports = router;