# System Overview

This document describes the architecture and functional design of the Acme Project Management Platform.
The platform includes a web-based frontend, multiple backend microservices, shared authentication mechanisms,
and cloud-hosted infrastructure designed for horizontal scaling.

---

# High-Level Goals

1. Provide an efficient task and project management solution.
2. Support thousands of concurrent users.
3. Offer fast, responsive UI using modern frontend technologies.
4. Provide secure, stable backend services using REST APIs.
5. Deploy infrastructure that allows continuous delivery and automated scaling.

---

# Frontend Architecture

The frontend is implemented as a Single Page Application built with React and TypeScript.
It uses a component-based architecture, global state managed with Redux Toolkit, and a custom UI library built
on top of TailwindCSS.

The UI consumes REST API endpoints exposed by the backend services. The application renders pages such as:

- Dashboard
- Project Overview
- Task Board
- Admin Settings
- User Profile

Performance considerations include client-side caching, memoized components, and virtualization for large lists.

## Frontend Routing

Routing uses react-router v6 with both static and dynamic routes.
Authentication state determines whether a user can access protected routes such as `/projects/:id`.

## State Management

We use Redux Toolkit for global state and React Query for server state and caching.
Key slices include:
- `authSlice`
- `projectSlice`
- `tasksSlice`
- `uiSlice`

## Component Library

A custom design system provides reusable components including:
- Buttons
- Panels
- Modal dialogs
- Dropdowns
- Avatar components
- Layout grids

## Frontend Security Measures

Frontend security includes:
- Sanitization of untrusted input
- Avoiding `dangerouslySetInnerHTML`
- CSRF token injection from backend
- Strict Content Security Policy (CSP)
- Using HTTPS for all API calls

---

# Backend Architecture

The backend consists of several microservices, written in C# using ASP.NET Core.

Core services include:

- **User Service**: authentication, JWT tokens, profile management.
- **Project Service**: CRUD operations for projects.
- **Task Service**: task creation, assignment, comments.
- **Notification Service**: email/push notifications.

Services communicate via REST APIs and publish domain events to a message bus for asynchronous workflows.

## Authentication Flow

Authentication uses OAuth 2.1 with Authorization Code Flow.
JWT tokens are signed using RS256 and validated by all backend services.

## API Design Principles

- RESTful endpoints
- Clear resource-based URLs
- Versioned APIs via `/api/v1/`
- Pagination enforced on list responses
- Validation using FluentValidation
- Consistent error responses with problem details

## Data Persistence

The platform uses PostgreSQL for transactional data and Redis for caching.
Entity relationships use EF Core with code-first migrations.

---

# Infrastructure & Deployment

Infrastructure is managed with IaC using Terraform and deployed to a Kubernetes cluster.
The cluster is hosted on a cloud provider and includes:

- Ingress controller (NGINX)
- Horizontal Pod Autoscaler (HPA)
- Persistent Volume Claims for PostgreSQL
- Redis cluster
- Managed message broker (RabbitMQ)

CI/CD is implemented with GitHub Actions and ArgoCD handles deployment.

## Logging & Monitoring

Monitoring is done with Prometheus and Grafana dashboards.
Logs are stored in an ELK stack and queryable via Kibana.

---

# Security Considerations

Security is enforced at multiple layers.

## Backend Security

Backend services must:
- Validate all input, including JSON payloads
- Use parameterized queries
- Enforce RBAC (role-based access control)
- Rotate signing keys
- Apply rate limiting on sensitive endpoints
- Reject outdated tokens immediately

## Infrastructure Security

Infrastructure must:
- Restrict traffic using Kubernetes Network Policies
- Apply secrets management using Vault
- Enable TLS termination at the ingress layer
- Perform nightly vulnerability scans
- Require MFA for admin access

---

# Workflows

## User Creates a Task

1. User clicks "Create Task" in the React UI.
2. UI validates required fields.
3. UI submits POST `/api/v1/tasks`.
4. Backend Task Service validates body.
5. Task is saved in PostgreSQL.
6. Event is published to RabbitMQ.
7. Notification Service sends confirmation email.

## User Logs In

1. User enters credentials in the login form.
2. UI calls `/api/v1/auth/login`.
3. Backend verifies password and returns JWT.
4. UI stores token in memory only.
5. Token enables protected routes.

---

# Glossary

- **SPA**: Single Page Application
- **JWT**: JSON Web Token
- **HPA**: Horizontal Pod Autoscaler
- **RBAC**: Role-Based Access Control

---

# Mixed Sections to Challenge Topic Extraction

The frontend occasionally communicates with the backend using long polling for specific real-time updates,
although WebSocket support is planned for later versions. Frontend performance requires reducing the number of
network calls.

From an infrastructure standpoint, scaling the Task Service requires CPU-based auto-scaling triggers in Kubernetes,
but frontend caching logic can further reduce load.

Security also plays a role: both frontend and backend must enforce strict validation of user input.

A shared "Audit Log" pipeline aggregates events from all microservices but is also partially exposed to frontend admin users.
