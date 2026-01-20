const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
require('dotenv').config();

const ticketsRouter = require('./routes/tickets');
const usersRouter = require('./routes/users');

const app = express();

app.use(cors({ origin: process.env.CORS_ORIGIN, credentials: true }));
app.use(express.json());
app.use(morgan('dev'));

app.get('/health', (req, res) => res.json({ status: 'ok' }));

app.use('/api/users', usersRouter);
app.use('/api/tickets', ticketsRouter);

const port = process.env.PORT || 4000;
app.listen(port, () => console.log(`Server running on port ${port}`));