const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { body, validationResult } = require('express-validator');
const pool = require('../db/pool');

const router = express.Router();

// Register
router.post(
  '/register',
  [
    body('name').isLength({ min: 2 }),
    body('email').isEmail(),
    body('password').isLength({ min: 6 }),
    body('role').isIn(['student','staff','admin']),
  ],
  async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) return res.status(400).json({ errors: errors.array() });

    const { name, email, password, role } = req.body;
    const hash = await bcrypt.hash(password, 10);

    try {
      const { rows } = await pool.query(
        'INSERT INTO users (name, email, role, password_hash) VALUES ($1,$2,$3,$4) RETURNING id, name, email, role',
        [name, email, role, hash]
      );
      res.status(201).json(rows[0]);
    } catch (e) {
      if (e.code === '23505') return res.status(409).json({ error: 'Email already exists' });
      res.status(500).json({ error: 'Server error' });
    }
  }
);

// Login
router.post('/login', [body('email').isEmail(), body('password').notEmpty()], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) return res.status(400).json({ errors: errors.array() });

  const { email, password } = req.body;
  const { rows } = await pool.query('SELECT * FROM users WHERE email=$1', [email]);
  const user = rows[0];
  if (!user) return res.status(401).json({ error: 'Invalid credentials' });

  const ok = await bcrypt.compare(password, user.password_hash);
  if (!ok) return res.status(401).json({ error: 'Invalid credentials' });

  const token = jwt.sign({ id: user.id, role: user.role, name: user.name }, process.env.JWT_SECRET, { expiresIn: '8h' });
  res.json({ token, user: { id: user.id, name: user.name, email: user.email, role: user.role } });
});

module.exports = router;