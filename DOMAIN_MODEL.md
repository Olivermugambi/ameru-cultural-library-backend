# Domain Model

Canonical vocabulary shared with the frontend.

Core resources: `Book`, `Author`, `Contributor`, `Theme`, `Collection`, `Artifact`, `Place`, `Article`, `LearningItem`, `Quiz`, `Program`, `MediaAsset`, and `Source`.

Baraza resources: `BarazaConcept`, `BarazaInquiry`, `BarazaText`, `BarazaThinker`.

Community is conditional and must not be introduced as a synonym for Baraza.

## Content status
Every published resource must have an explicit lifecycle status such as `draft`, `review`, `published`, or `archived`.

## Epistemic status
Where meaningful, content distinguishes:
- `source`: supplied/archival source material
- `editorial`: curated editorial framing
- `interpretation`: reasoned interpretation
- `contemporary`: present-day contribution
- `speculative`: explicitly exploratory material

These labels describe the status of a claim or representation; they do not automatically establish truth or cultural authority.

## Relationships
Resources should link through stable identifiers rather than embedding duplicated copies of other resources. A book can relate to themes, contributors, collections, media, sources, and other cultural resources. Artifacts can relate to places, themes, sources, media, books, and programs. Baraza resources can relate to texts, thinkers, books, artifacts, and inquiries.

## Identity
IDs are opaque API identifiers. Slugs may be exposed for navigation but are not authoritative identities.

## Rule
Do not add a domain entity merely because a screen needs a label. Add it when it represents a stable concept or relationship in the cultural information model.
