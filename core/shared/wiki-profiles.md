# Wiki kind profiles

Each wiki has a `kind` that determines its concept taxonomy and what to extract during
ingest. Use the matching profile.

## kind: project
Source: meeting minutes, SOPs, product/feature docs, as-is workflow descriptions, decisions.
Concept types & what to extract:
- **process** — as-is workflows, step by step, with actors and systems touched.
- **decision** — decisions and rationale mined from meeting minutes (one article each).
- **product** — features/capabilities described in product docs.
- **term** — domain vocabulary → also list in `glossary.md`.
- **standard** — internal policies, compliance, UX standards referenced by the project.
Link out to shared wikis: `[[integrations:…]]`, `[[devops:…]]`, `[[codebase:…]]`.

## kind: integrations
Source: integration specs, API docs, IT/infra docs. One concept article per integration.
Concept types: **integration** (subtype in body). Extract for each:
- **SSO** — provider (Okta/Azure AD/…), protocol (SAML/OIDC), flows, attributes/claims,
  provisioning (SCIM), environments.
- **APIs** — internal vs external, base URLs, auth (OAuth/API-key/mTLS), rate limits,
  pagination, key endpoints, versioning, owners.
- **Email** — provider (SES/SendGrid/SMTP), sending domains, templates, bounce/complaint
  handling, limits.
- **FTP/SFTP** — hosts, credentials model, directory layout, file formats, schedules,
  retry/error handling.
- **Webhooks/messaging** — events, payloads, delivery guarantees, signing.
Record data exchanged, direction, and which systems depend on each integration.

## kind: devops
Source: pipeline configs, runbooks, infra docs, release notes.
Concept types:
- **pipeline** — CI/CD stages, triggers, gates, artifacts.
- **environment** — dev/stage/prod, topology, config/secrets management.
- **process** — deploy, rollback, release, incident, on-call/runbooks.
- **observability** — logging, metrics, alerting, SLOs.
- **standard** — security/compliance controls in the pipeline.

## kind: codebase
Source: an existing code repository (cloned via the registry). Walk the tree; do NOT paste
code — describe. Concept types:
- **service / module** — one article per service or top-level module: responsibility,
  entrypoints, key files, owners.
- **api / endpoint** — public interfaces (HTTP routes, gRPC, CLI, events) with inputs/outputs.
- **data model** — important entities/schemas/tables and relationships.
- **config** — environment variables, feature flags, config files.
- **dependency** — notable external libraries/services and why.
- **integration** — link to `[[integrations:…]]` where the code calls an integration.
Derive Jira **Components** from services/modules here (see jira-organization.md).

## kind: custom
Define your own concept types in the wiki's `index.md`; keep frontmatter `type` consistent.
