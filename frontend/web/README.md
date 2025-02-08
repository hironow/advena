# web

web client for advena.

## Development

```sh
mr fe:update

mr fe:dev
mr fe:format
mr fe:test

mr fe:build:dev
```

## env

| Name | Description | Default | Required |
|------|-------------|---------|:--------:|
| `AUTH_SECRET` | auth.js random secret | - | ✓ |
| `AUTH_URL` | auth.js standalone use url | - | ✓ |
| `AUTH_TRUST_HOST` | auth.js standalone must true | - | ✓ |
| `FIREBASE_CLIENT_EMAIL` | firebase admin client email | - | ✓ |
| `FIREBASE_PRIVATE_KEY` | firebase admin private key | - | ✓ |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | next.js firebase client api key | - | ✓ |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | next.js firebase client auth domain | - | ✓ |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | next.js firebase client project id | - | ✓ |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | next.js firebase client storage bucket | - | ✓ |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | next.js firebase client messaging sender id | - | ✓ |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | next.js firebase client app id | - | ✓ |
| `NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID` | next.js firebase client measurement id | - | ✓ |
| `NEXT_PUBLIC_GOOGLE_ANALYTICS_ID` | next.js google analytics id | - | ✓ |