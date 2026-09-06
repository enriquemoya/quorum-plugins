# Partner intake

Fill every field before generating. Anything left blank becomes an explicit
`TODO(partner-intake)` in the generated code — never a guess.

## Identity

| Field | Value |
|---|---|
| Display name | |
| Code identifier `{Partner}` | |
| Partner-side system of record | |
| Pipelines needed | |

## Authentication

| Field | Value |
|---|---|
| Scheme (OAuth2 / API key / mTLS / basic) | |
| Token endpoint (if applicable) | |
| Token lifetime + refresh rule | |
| Credential field **names** (never values) | |
| Sandbox credentials available? | |

## Endpoints

One row per operation. Attach a real sample request and response for each —
a schema description is not a substitute for a payload you have seen.

| Operation | Method + path | Request shape | Response shape | Notes |
|---|---|---|---|---|
| | | | | |

## Field mapping

| Partner field | Our field | Transform | Required? | On missing |
|---|---|---|---|---|
| | | | | |

Record the transform explicitly, including units, timezone, and null handling.
"Same thing, different name" is a transform worth writing down.

## Operational semantics

| Field | Value |
|---|---|
| Rate limit | |
| Pagination style | |
| Idempotency (key? replay-safe?) | |
| Error taxonomy (retryable vs terminal) | |
| Expected volume | |

## Open questions

Anything the partner has not answered. Each becomes a `TODO(partner-intake)`.

- [ ]
