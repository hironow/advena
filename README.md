# advena

[![Build](https://github.com/hironow/advena/actions/workflows/build.yaml/badge.svg)](https://github.com/hironow/advena/actions/workflows/build.yaml) [![Test](https://github.com/hironow/advena/actions/workflows/test.yaml/badge.svg)](https://github.com/hironow/advena/actions/workflows/test.yaml)

<p align="center">
    コードネーム: advena アドヴェナ
</p>

## Preparing for development

Install [mise](https://github.com/jdx/mise), and add aliases:

```bash
# ~/.zshrc or ~/.bashrc etc.
alias mx="mise exec --"
alias mr="mise run"
```

Install [dotenvx](https://github.com/dotenvx/dotenvx):

current using versions:

```bash
mise --version
2025.1.4 macos-arm64 (2f78ee6 2025-01-10)

dotenvx --version
1.26.0
```

Install [firebase-tools](https://github.com/firebase/firebase-tools):

```bash
curl -sL firebase.tools | bash
```

### Install dependencies

```bash
# frontend (fe, as shorthand)
mr fe:update
# backend (be, as shorthand)
mr be:update
```

## Start development

```bash
# start emulator (firebase auth, firestore, storage, etc)
mr f:emulator

# open vscode (as shorthand)
mr c

# start
mr fe:dev
mr be:dev

# format
mr fe:format
mr be:format

# test
mr fe:test
mr be:test
```

run tasks in parallel:

```bash
# frontend and backend
mr fe:dev ::: be:dev

# format and test
mr fe:format ::: be:format ::: fe:test ::: be:test
```

### Add dependencies

frontend uses [pnpm](https://github.com/pnpm/pnpm):

```bash
# frontend
cd frontend/web/
mx pnpm add <package-name>
mx pnpm add --save-dev <package-name>
```

backend uses [uv](https://github.com/astral-sh/uv):

```bash
# backend
cd backend/genai/
mx uv add <package-name>
mx uv add --dev <package-name>
```

## google cloud

### setup

```bash
# login (with load application default credentials, as shorthand)
mr g:login

# set confiture (only first, as shorthand)
mr g
```

if you want anther configuration, you can use:

```bash
gcloud config configurations create <your-configuration-name>
```

### build

build docker image and push to google artifact registry

wip

### deploy

deploy to google cloud run and other components(like firestore, storage, eventarc, firebase, etc)

wip

## references

* [chose AI on Google Cloud](https://cloud.google.com/docs/generative-ai/choose-models-infra-for-ai)
* [firestore practices](https://cloud.google.com/firestore/docs/best-practices)
* [Laminar LLM Tracing](https://docs.lmnr.ai/overview)
  * [projects](https://www.lmnr.ai/projects)
* [W&B Weave Tracking](https://weave-docs.wandb.ai/)
  * [projects](https://wandb.ai/home)
* [Next.js convention with dotenvx](https://dotenvx.com/docs/advanced/run-convention)
* ...

## trouble shooting

### tips: re-login gcloud and firebase

```bash
gcloud auth login
gcloud auth application-default login
firebase login
```
