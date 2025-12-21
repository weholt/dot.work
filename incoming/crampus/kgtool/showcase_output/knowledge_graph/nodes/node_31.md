# 10. Cross-domain mixed content (for testing classification)

**Tags:** backend

**Keywords:** backend, frontend, using, service, based cluster, failures, exposed partly, experience isolated

**Keyphrases:** cluster HPA rules, scale differently based, HPA rules, queries using RTQ, cluster HPA, frontend requires caching, requires caching, scale differently, differently based, based on cluster

---

The frontend requires caching of backend queries using RTQ, while the backend inventory service may scale
differently based on cluster HPA rules. Infrastructure failures may affect frontend user experience if not isolated
using service mesh timeouts. Compliance also mandates audit logs exposed partly via the frontend admin panels
but enforced through backend IAM.

---