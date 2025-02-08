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