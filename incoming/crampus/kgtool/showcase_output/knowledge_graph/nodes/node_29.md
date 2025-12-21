# 8.2 Document Upload Workflow

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