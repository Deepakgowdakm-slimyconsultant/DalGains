import createClient from "openapi-fetch";
import type { paths } from "./schema.gen";

// Typed client generated from the FastAPI OpenAPI schema
// (schema.gen.ts, via `npm run generate-api`) -- no hand-rolled,
// untyped fetch calls. Regenerate after any backend route change:
//   python -m scripts.export_openapi_schema   (from repo root)
//   npm run generate-api                       (from frontend/)
export const api = createClient<paths>({
  baseUrl: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
});
