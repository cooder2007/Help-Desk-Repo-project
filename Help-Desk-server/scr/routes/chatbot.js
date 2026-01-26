const express = require('express');
const auth = require('../middleware/auth');
const { detectIntent } = require('../chatbot/chatbot');

const router = express.Router();

router.post('/', auth(['student','staff','admin']), (req, res) => {
  const { message } = req.body;
  if (!message) return res.status(400).json({ error: 'Message required' });

  const reply = detectIntent(message);
  res.json({ reply });
});

module.exports = router;
