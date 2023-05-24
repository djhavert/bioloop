const express = require('express');

const { authenticate } = require('../middleware/auth');

const router = express.Router();

router.get('/health', (req, res) => { res.send('OK'); });
router.use('/auth', require('./auth'));
router.use('/reports', require('./reports'));

// From this point on, all routes require authentication.
router.use(authenticate);

router.use('/datasets', require('./datasets'));
router.use('/metrics', require('./metrics'));
router.use('/users', require('./users'));
router.use('/workflows', require('./workflows'));

module.exports = router;