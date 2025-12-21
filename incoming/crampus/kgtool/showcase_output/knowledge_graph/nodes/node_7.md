# 3.3 State Management

**Tags:** data

**Keywords:** state, recoil, server, state redux, redux, redux toolkit, toolkit, ui

**Keyphrases:** Redux Toolkit Query, BroadcastChannel API Guidelines, API Guidelines include, Redux Toolkit, calls inside components, Remote server state, direct fetch calls, fetch calls inside, Service Hooks, Toolkit Query

---

Global state uses a hybrid model:

- Business state → Redux Toolkit
- Remote server state → Redux Toolkit Query
- Ephemeral UI state → Recoil
- Cross-tab sync → BroadcastChannel API

Guidelines include:

- No direct fetch calls inside components  
- All server interactions via unified "Service Hooks"  
- UI mutation goes through RTL reducers or Recoil atoms