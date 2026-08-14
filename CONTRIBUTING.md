# Contributing

Read `ARCHITECTURE.md`, `DOMAIN_MODEL.md`, `CONTENT_GOVERNANCE.md`, and `MEDIA_POLICY.md` before changing domain or API behavior.

Every feature should include tests and preserve the full verification gate. Prefer extending an existing domain model or service over adding parallel concepts. API changes must update the relevant contract documentation.

Never invent cultural, historical, provenance, attribution, or licensing facts to make fixtures look realistic. Clearly label synthetic fixtures.

Do not couple frontend presentation concerns to backend domain models. Do not add authentication, CMS, moderation, or persistence infrastructure unless the corresponding product scope has been approved.
