# DalGains frontend

React + Vite + TypeScript, mobile-first, PWA-capable. Pairs with the
FastAPI backend in `src/api/`.

## Design tokens

`tailwind.config.ts` reads `../design/tokens/*.json` directly at build
time (colors, typography, spacing) -- there are no hand-tuned Tailwind
defaults or one-off hex codes in this project. To change a color, font,
or spacing value, edit the token JSON, not this project.

## i18n

Locale strings live in `src/i18n/locales/*.json` at the repo root (owned
by the backend's `src/i18n/loader.py`) -- not duplicated here. `npm run
sync-locales` (also run automatically before `dev`/`build`) copies them
into `public/locales/<lng>/translation.json`, which `react-i18next`'s
http backend fetches at runtime. `public/locales/` is generated and
gitignored.

English (`en`) is the default locale everywhere; Hindi and Kannada are
opt-in, switched via the language switcher in Profile/Settings. See
`src/i18n/README.md` at the repo root for the full precedence rule.

## API client

`src/api/schema.gen.ts` is generated from the backend's OpenAPI schema
and is committed so the frontend typechecks without the backend running.
Regenerate after any backend route change:

```
python -m scripts.export_openapi_schema   # from repo root, writes openapi.json
npm run generate-api                       # from frontend/, reads ../openapi.json
```

`src/api/client.ts` wraps the generated types in a typed `openapi-fetch`
client -- no hand-rolled untyped `fetch` calls against the API.

## Scripts

- `npm run dev` -- start the Vite dev server (default `http://localhost:5173`, already allowed by the backend's CORS config)
- `npm run build` -- typecheck + production build
- `npm run lint` -- oxlint
