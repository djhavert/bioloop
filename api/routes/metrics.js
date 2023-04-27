const express = require('express');
const { PrismaClient } = require('@prisma/client');

const asyncHandler = require('../middleware/asyncHandler');

const router = express.Router();
const prisma = new PrismaClient();

router.get('/latest', asyncHandler(async (req, res, next) => {
  // #swagger.tags = ['Metrics']
  // #swagger.summary = 'Get latest entries for each measurement.'
  const latestEntries = await prisma.$queryRaw`
    select distinct on (measurement, subject) timestamp, measurement, subject, usage, "limit", fields, tags
    from metric
    order by measurement, subject, timestamp desc;
  `;

  res.json(latestEntries);
}));

router.post('/', asyncHandler(async (req, res, next) => {
  // #swagger.tags = ['Metrics']
  // #swagger.summary = 'Insert new measurements'
  const result = await prisma.metric.createMany({
    data: req.body,
  });
  res.json(result);
}));

module.exports = router;
