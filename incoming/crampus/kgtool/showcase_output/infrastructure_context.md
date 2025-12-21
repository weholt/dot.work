# Topic Context: infrastructure

Extracted 4 nodes.

---

## [8] 3.4 Frontend Security

**Tags:** infrastructure

**Keywords:** tokens, bearer, html enforce, html, gating rely, idle timeout, idle, gating

**Keyphrases:** Reject untrusted HTML, Enforce strict CSP, Validate user permissions, user permissions client-side, Require re-authentication, Reject untrusted, untrusted HTML, Enforce strict, strict CSP, Validate user

---

Frontend must:

- Never store tokens in localStorage  
- Use `Authorization: Bearer` + memory-only tokens  
- Require re-authentication after idle timeout  
- Reject untrusted HTML  
- Enforce strict CSP  
- Validate user permissions client-side (UI gating), but never rely solely on it  

---

## [13] 4.4 Document Processing Service

**Tags:** infrastructure

**Keywords:** ocr, image, image ocr, extraction image, extraction, engine tesseract, enforcement dependencies, enforcement

**Keyphrases:** Retention policy enforcement, policy enforcement Dependencies, PDF extraction, Tesseract cluster, Image OCR, OCR Engine, Retention policy, enforcement Dependencies, raw documents, work queue

---

Supports:

- PDF extraction  
- Image OCR  
- Classification  
- Retention policy enforcement  

Dependencies:

- S3 (raw documents)  
- Redis (work queue)  
- OCR Engine (Tesseract cluster)

## [28] 8.1 Resource Scheduling Workflow

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

## [29] 8.2 Document Upload Workflow

**Tags:** infrastructure

**Keywords:** file, indexed, log entry, log, file upload, file s3, indexed search, entry emitted

**Keyphrases:** Upload API, SPA sends, SPA, API, User uploads, file, OCR is scheduled, Storage, Storage service, SPA sends file

---

1. User uploads via DropZone.  
2. SPA sends file to Upload API.  
3. Storage service streams file to S3.  
4. OCR is scheduled.  
5. Classification runs.  
6. Document indexed in search.  
7. Audit log entry emitted.  

---

