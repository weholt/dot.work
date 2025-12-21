# intro?

This doc contains SOME info about frontend/backend but also weird stuff.

Like:
React?? yes. But also tables about servers. And a bit about CSS but in the same paragraph we talk about Kubernetes pods and database indexes.

## Random Section: performance or security??

Sometimes we talk about API endpoints:
/api/user/create  
/api/user/delete  

Then suddenly this paragraph talks about designing color palettes for the React components,
and then about rotating TLS certificates in the same sentence.

Performance note: "Use memoization in React" right next to "use indexed JOINs on PostgreSQL tables".

### backend? frontend? nobody knows.

The backend must validate everything. The frontend must show buttons? maybe?  
We also mention Kafka topics here for no reason.

And then some UI/UX rules:
- Don't use popups
- Keyboard navigation needed

Immediately followed by:
- Nodes in Kubernetes should run with read-only root filesystem

And then:
AND THEN the doc says "Apply CSS grid for layout" and "Enable PodSecurity admission".

## Infrastructure… or maybe UX?

The cluster autoscaler should do its thing.  
Frontend bundling should happen with Vite.  

JWT tokens maybe?  
Dropdown component styling maybe?  

This document is a nightmare for classification.

## tables?

Sometimes tables are inline:

| Feature | Layer |
|--------|-------|
| Button | frontend |
| SQL index | backend |
| Ingress | infra |
| Hover styles | ?? |

## Final random notes

RTQ = Remote Task Queue.  
SPA = Single Page Application.  
TLS = security.  
Kafka = events.  
"hot reload" = frontend.
