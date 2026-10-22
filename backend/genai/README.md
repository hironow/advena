# genai

genai server for advena.

## Development

```sh
mr be:update

mr be:dev
mr be:format
mr be:test

mr be:gen

mr be:build:dev
```

## env

| Name | Description | Default | Required |
|------|-------------|---------|:--------:|
| `LMNR_PROJECT_API_KEY` | Laminar API key | - | ✓ |
| `WEAVE_PROJECT_NAME` | wandb weave project name | - | ✓ |
| `WANDB_API_KEY` | wandb api key | - | ✓ |
| `GOOGLE_CLOUD_PROJECT` | google cloud project | - | ✓ |
| `GOOGLE_CLOUD_LOCATION` | google cloud location | - | ✓ |
| `GOOGLE_CLOUD_STORAGE_BUCKET` | google cloud storage bucket | - | ✓ |
| `GOOGLE_CLOUD_SELF_ENDPOINT_URL` | google cloud cloud run self endpoint url | - | ✓ |
| `GEMINI_MODEL` | Model used by the dataset agent | `gemini-3.8-flash` | - |
| `GOOGLE_GENAI_USE_ENTERPRISE` | Set `true` to use Vertex AI / Agent Platform with ADC | - | For ADC |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` | Gemini Developer API key (`GOOGLE_API_KEY` takes precedence) | - | For API-key auth |

The dataset agent calls Google's SDK directly through `GeminiModel`; LiteLLM is
not installed. Authentication is selected by the SDK environment, not inferred
from the presence of `GOOGLE_CLOUD_PROJECT`:

- For Vertex AI / Agent Platform, set `GOOGLE_GENAI_USE_ENTERPRISE=true`,
  `GOOGLE_CLOUD_PROJECT`, and `GOOGLE_CLOUD_LOCATION`, and provide Application
  Default Credentials (the Cloud Run service account in deployment). The SDK
  also accepts the legacy `GOOGLE_GENAI_USE_VERTEXAI=true` flag; do not set
  conflicting provider flags.
- The supplied `.env`, `.env.dev`, and `.env.prd` select ADC with
  `GOOGLE_GENAI_USE_ENTERPRISE=true`, matching their existing GCP project/location.
- For the Gemini Developer API, override `GOOGLE_GENAI_USE_ENTERPRISE=false`,
  leave the legacy flag unset, and provide `GOOGLE_API_KEY` or `GEMINI_API_KEY`.
  With no env file loaded, both provider flags may instead remain unset.

Project/location alone are insufficient for SDK authentication. Configure one
of these modes before running or deploying the service. Tests exercise both
SDK selections with isolated environment variables and substitute credentials;
they do not establish live model availability, IAM access, or response quality.