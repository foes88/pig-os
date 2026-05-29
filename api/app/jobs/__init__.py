"""
ARQ background jobs.

Worker entry point:
  arq app.jobs.worker.WorkerSettings

Available job queues:
  - kpi     : KPI snapshot aggregation (daily/weekly/monthly)
  - notify  : Push/email notification dispatch
"""
