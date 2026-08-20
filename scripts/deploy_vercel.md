# Deploying the frontend to Vercel

Step-by-step, meant to be followed manually. Free tier, no credit
card, no sleeping, auto-deploys on every push once connected.

## 1. Create a Vercel account

Go to [vercel.com/signup](https://vercel.com/signup) and sign up
**via GitHub** (not email) -- this is what lets Vercel auto-deploy on
push without a separate CI setup, and needs no credit card.

## 2. Import the repository

1. [vercel.com/new](https://vercel.com/new) -> find and select the
   DalGains repo (grant Vercel access to it if this is the first time).
2. **Root Directory**: click **Edit** next to it and set it to
   `frontend` -- this repo is a monorepo (Python backend at the root,
   the Vite app under `frontend/`), and Vercel needs to know the
   frontend's `package.json` isn't at the repo root.
3. **Framework Preset**: Vercel auto-detects **Vite** once the root
   directory is set correctly (it reads `frontend/package.json` and
   `frontend/vite.config.ts`). Build command and output directory are
   also already declared in `frontend/vercel.json` (`npm run build`,
   `dist`) -- Vercel picks those up regardless of the auto-detected
   preset, so nothing to change here even if the preset shows
   differently.
4. Don't click Deploy yet -- set the environment variable first (next
   step), since the build needs it.

## 3. Set the environment variable

Still on the import screen (or later: Project -> **Settings** ->
**Environment Variables**):

| Name | Value |
|---|---|
| `VITE_API_URL` | Your Hugging Face Space's URL from `deploy_hf_spaces.md` step 8, e.g. `https://your-username-dalgains-api.hf.space` (no trailing slash) |

Apply it to all three environments (Production, Preview, Development)
unless you specifically want preview deploys hitting a different
backend.

## 4. Deploy

Click **Deploy**. Every push to your repo's default branch redeploys
Production automatically from here on; every other branch/PR gets its
own preview URL.

## 5. Note the deployed URL

Once the build finishes, Vercel shows the live URL:
`https://{project-name}.vercel.app` (or a custom domain if you add
one later). **Note this URL** -- it needs to go into the backend's
`CORS_ALLOWED_ORIGINS` (and, if you haven't already, `APP_URL`) in HF
Spaces' Settings -> Variables and secrets (`deploy_hf_spaces.md` step
7). Without that, every API call from this frontend will be blocked by
CORS -- see the verification step below for what that looks like.

## 6. Verify the frontend actually reaches the backend

1. Open the deployed `*.vercel.app` URL.
2. Open your browser's DevTools -> **Network** tab, reload the page.
3. Look for requests to your HF Spaces URL (e.g. a `GET .../health` or
   the onboarding flow's `POST .../profile`).
4. **Success**: the request shows status 200 (or whatever the route
   normally returns) with real response data.
5. **CORS not configured yet**: the request shows as failed in the
   Network tab with a console error like `has been blocked by CORS
   policy: No 'Access-Control-Allow-Origin' header is present`. Fix:
   add this exact Vercel URL to `CORS_ALLOWED_ORIGINS` in the HF Space
   settings (step 5 above), save (triggers an automatic Space restart),
   then reload the frontend.
6. Try logging in end-to-end (email -> check inbox for the magic link
   -> click it) to confirm the whole auth round trip works across the
   two domains, not just a simple GET.

## PWA manifest + service worker

`frontend/public/manifest.json` and the generated service worker
(`vite-plugin-pwa`, `registerType: "autoUpdate"`) both use
origin-relative paths -- neither hardcodes `localhost` or any specific
deployed URL, so they need no per-environment configuration. Two things
worth confirming after this first deploy, though:

- **Manifest**: open DevTools -> Application tab -> Manifest, confirm
  the icon, name, and theme color load correctly from the deployed
  origin (not a broken/relative-path issue that only shows up once
  actually deployed under a real domain+path).
- **Service worker updates on redeploy**: `registerType: "autoUpdate"`
  means the browser checks for a new service worker on every page
  load and activates it automatically (no "update available, please
  refresh" prompt to build) -- after a second deploy, reload the app
  twice (the first reload detects and installs the new SW, the second
  is served by it) and confirm DevTools -> Application -> Service
  Workers shows the new version as active, not stuck on the old one.

---

**Session note**: same as `deploy_hf_spaces.md` -- this session doesn't
have your Vercel/GitHub credentials and can't click through this UI on
your behalf. `frontend/vercel.json` and this doc are the parts
prepared in advance; steps 1-6 are yours to run.
