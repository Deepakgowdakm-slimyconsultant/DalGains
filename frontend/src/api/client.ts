import createClient from "openapi-fetch";
import type { paths } from "./schema.gen";

// Typed client generated from the FastAPI OpenAPI schema
// (schema.gen.ts, via `npm run generate-api`) -- no hand-rolled,
// untyped fetch calls. Regenerate after any backend route change:
//   python -m scripts.export_openapi_schema   (from repo root)
//   npm run generate-api                       (from frontend/)
export const api = createClient<paths>({
  baseUrl: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  // openapi-fetch defaults to `fetch: globalThis.fetch`, captured once
  // when createClient() runs (module-import time, here). MSW's
  // server.listen() (component tests) patches globalThis.fetch later,
  // in a beforeAll -- an eagerly-captured reference would miss that
  // patch entirely and hit the real network. Resolving `fetch` inside
  // the wrapper instead of as a default-parameter value looks it up
  // fresh on every call, after MSW is listening.
  fetch: (...args: Parameters<typeof fetch>) => fetch(...args),
});
