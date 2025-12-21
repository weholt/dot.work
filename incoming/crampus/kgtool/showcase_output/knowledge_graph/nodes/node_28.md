# 8.1 Resource Scheduling Workflow

**Tags:** infrastructure

**Keywords:** event, kafka event, backend validates, event scheduleapplied, engine updates, emitted analytics, consumes event, consumes

**Keyphrases:** SPA sends POST, SPA sends, sends POST, SPA, POST, event, Frontend user selects, Kafka event, Backend validates, api

---

1. Frontend user selects resources on timeline.  
2. SPA sends POST `/api/v2/schedule/apply`.  
3. Backend validates business rules.  
4. Scheduler engine updates aggregates.  
5. Kafka event `ScheduleApplied` emitted.  
6. Analytics pipeline consumes event.