# Media Policy

Media is a first-class content resource. The API describes how an asset should be presented without forcing the frontend to infer intent from filenames.

## Display semantics
- `cover`: cropping may be used when it does not remove semantically important information.
- `contain`: the complete object must remain visible. Use for book covers and culturally significant objects when the full form matters.
- `gallery`: preserve contextual framing and allow inspection of multiple views.

## Metadata
A media asset may carry source URL, attribution, licensing information, alt text, dimensions, MIME type, and an optional focal point. Unknown rights or attribution must not be fabricated.

## Delivery
The backend should expose stable metadata and URLs/identifiers. Image transformation/CDN implementation remains an infrastructure concern.

## Accessibility
Meaningful media requires useful alternative text. Decorative media must be explicitly marked decorative rather than receiving guessed descriptions.

## Rule
Do not crop an artifact or book cover merely to satisfy a fixed UI aspect ratio. The consumer must be able to honor the semantic display mode.
