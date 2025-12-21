# 3.4 Frontend Security

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