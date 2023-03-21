const express = require('express');
// const { PrismaClient } = require('@prisma/client');

const asyncHandler = require('../middleware/asyncHandler');
const wf_service = require('../services/workflow');
const { accessControl } = require('../middleware/auth');

const isPermittedTo = accessControl('workflow');

const router = express.Router();
// const prisma = new PrismaClient();

router.get(
  '/',
  isPermittedTo('read', false),

  asyncHandler(
    async (req, res, next) => {
      const api_res = await wf_service.getOne(
        req.query.last_task_runs,
        req.query.prev_task_runs,
      );
      res.json(api_res.data);
    },
  ),
);

router.get(
  '/:id',
  isPermittedTo('read', false),

  asyncHandler(
    async (req, res, next) => {
      const api_res = await wf_service.getOne(
        req.params.id,
        req.query.last_task_runs,
        req.query.prev_task_runs,
      );
      res.json(api_res.data);
    },
  ),
);

router.post(
  '/:id/pause',
  isPermittedTo('update', false),

  asyncHandler(
    async (req, res, next) => {
      const api_res = await wf_service.pause(req.params.id);
      res.json(api_res.data);
    },
  ),
);

router.post(
  '/:id/resume',
  isPermittedTo('update', false),

  asyncHandler(
    async (req, res, next) => {
      const api_res = await wf_service.resume(req.params.id);
      res.json(api_res.data);
    },
  ),
);

router.delete(
  '/:id',
  isPermittedTo('delete', false),

  asyncHandler(
    async (req, res, next) => {
      const api_res = await wf_service.deleteOne(req.params.id);
      res.json(api_res.data);
    },
  ),
);

module.exports = router;