# Deploying the backend to Render

This deploys the React + FastAPI edition. For the parallel Streamlit
deployment (also free, no data loss), see `deploy_streamlit.md`
(added in a future session).

Step-by-step, meant to be followed manually. Written for someone who's
never used Render before but has a GitHub account and has already
signed up for Render (free, no credit card).

There are two sections below, for two different points in this app's
life:

- **Section 1: Free tier** -- what you deploy today, for looking at
  the real interface on a real phone. Data does not persist.
- **Section 2: Starter tier** -- the upgrade you make later, once the
  app is worth $7-8/month to keep alive with real data for family and
  friends.

---

## Section 1: Free tier deployment (current -- interface exploration only)

> **This deployment is for interface exploration only. All logged
> data (profiles, meal logs, calibrations) is wiped every time the
> service goes idle for 15 minutes and then wakes back up. Do NOT
> share this URL with users expecting real usage -- they will lose
> their data.** For family/friend use, deploy the Streamlit edition
> instead (see `deploy_streamlit.md`, added later) or upgrade to
> Section 2 below.

### 1. Prerequisites checklist

- [ ] Render account created (free, no card) -- [render.com](https://render.com/)
- [ ] The DalGains repo already exists on GitHub (it does)
- [ ] A Resend account + API key ready to grab when you get to the
      env-var step -- [resend.com](https://resend.com/), free tier,
      no card, 100 emails/day
- [ ] A `JWT_SECRET` generated locally -- run this and save the
      output somewhere for the next step:
      ```
      python -c "import secrets; print(secrets.token_urlsafe(48))"
      ```
- [ ] Your admin email chosen (the address you'll log in with, and
      that gets auto-made-admin on first boot)

### 2. Create the Web Service

1. Log into the [Render dashboard](https://dashboard.render.com/).
2. Click **New** (top right) -> **Web Service**. (Not **Static
   Site** -- that's for the frontend, and this repo's backend isn't
   static. Not **Private Service** -- that hides the service behind
   Render's internal network only, which we don't want here.)
3. **Connect GitHub**: if this is your first Render deploy, it'll ask
   you to authorize Render to access your GitHub account. Grant it
   access either to all repos or just to DalGains -- your call.
4. In the repo list/search, select the **DalGains** repo.
5. Render shows a form. Fill it in:

   | Field | Value |
   |---|---|
   | Name | `dalgains-api` (or anything you like -- this becomes part of the URL) |
   | Region | **Singapore** if it's listed as a free region at the time you deploy (closest to India); fall back to **Frankfurt** if not |
   | Branch | `main` |
   | Root Directory | leave blank -- the Dockerfile is at the repo root |
   | Runtime | **Docker** (Render auto-detects this from the `Dockerfile` once Root Directory is set) |
   | Instance Type | **Free** |

6. **Don't click "Create Web Service" yet.** Scroll down -- Render's
   create form usually has an **Environment Variables** section
   further down the same page, so you can set them before the first
   build runs. (If your version of the form doesn't show one, that's
   fine -- create the service first, then go to its **Environment**
   tab immediately after, before the first deploy finishes, and add
   them there. Either order works; just don't leave the app running
   in prod without `JWT_SECRET` set.)

### 3. Environment variables

Add each of these (in the create form's env var section, or the
**Environment** tab after creating the service):

| Key | Value | Secret? |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/dalgains.db` | no |
| `JWT_SECRET` | *(paste the 48-character string you generated in step 1)* | **yes** |
| `RESEND_API_KEY` | *(paste from your Resend account -- resend.com/api-keys)* | **yes** |
| `APP_URL` | `https://dalgains.vercel.app` *(placeholder -- you'll replace this with your real Vercel URL in step 7 below, after the Vercel deploy)* | no |
| `ADMIN_EMAIL` | *(your admin email from step 1)* | no |
| `ENVIRONMENT` | `prod` | no |
| `CORS_ALLOWED_ORIGINS` | `https://dalgains.vercel.app` *(same placeholder as `APP_URL` -- replaced in step 7)* | no |

Notes:

- `DATABASE_URL` here is the **same relative path used in local dev**
  (`sqlite:///./data/dalgains.db`) -- it resolves to `/app/data/` inside
  the container, which already exists in the image (that's where the
  seeded ingredient/recipe reference data lives). Nothing extra to
  create. This is deliberately *not* an absolute path into a mounted
  disk -- the free tier has no disk to mount (see step 4).
- Render's UI has a checkbox or toggle per variable marked **Secret**
  -- use it for `JWT_SECRET` and `RESEND_API_KEY` so their values are
  masked in the dashboard and build logs. The rest don't need it.

### 4. No persistent disk on this tier

Render's **Disks** tab only appears / only works for **paid** instance
types -- the Free instance type cannot attach a persistent disk at
all. That means the `/app/data/dalgains.db` SQLite file created in
step 3 lives on the container's local, ephemeral filesystem:

- It survives while the service is actively running and handling
  requests.
- **It is wiped every time the service spins down** (after ~15
  minutes with no incoming requests) **and comes back up fresh on
  the next request.** Same thing happens on every redeploy.
- Skip this step entirely for the free tier -- there is nothing to
  configure here. Move on to step 5.

If you want data to actually survive, that's Section 2 below.

### 5. Deploy and verify

1. Click **Create Web Service**. If you added env vars in step 3
   already, the first deploy kicks off automatically.
2. Watch the **Logs** tab (or the deploy's own log view). Expect
   **5-10 minutes** for the first build -- it's building the Docker
   image from scratch (installing `build-essential`, then every
   Python package in `requirements.txt`) and there's no cache yet.
3. Watch for the last couple of lines to show something like
   `Application startup complete` (uvicorn) -- that means migrations
   ran and the app is listening.
4. Once the dashboard shows the service status as **Live** (green),
   copy the URL Render assigned, shown near the top of the service
   page: `https://dalgains-api.onrender.com` (or whatever you named
   it in step 2).
5. Open `https://dalgains-api.onrender.com/health` in your browser.
   You should see JSON like:
   ```json
   {"status": "ok", "ingredient_count": 1234, "recipe_count": 8, "version": "0.4.0", "admin_contact": "you@example.com"}
   ```
6. **If `/health` errors out or the deploy never goes Live**: open the
   **Logs** tab and look for the `alembic upgrade head` line near the
   start of the container's output (the `Dockerfile`'s `CMD` runs
   migrations before starting uvicorn) -- a traceback there, not a
   normal uvicorn startup line, means the database schema step
   failed. See the Troubleshooting section below.

### 6. Note this URL

You'll paste `https://dalgains-api.onrender.com` (your real assigned
URL) into Vercel as `VITE_API_URL` in `deploy_vercel.md`'s deploy
steps.

### 7. Coming back after the Vercel deploy

Once Vercel gives you a real URL like `https://dalgains.vercel.app`
(see `deploy_vercel.md`):

1. Come back to this Render service -> **Environment** tab.
2. Update `CORS_ALLOWED_ORIGINS` to your real Vercel URL (replacing
   the placeholder from step 3).
3. Update `APP_URL` the same way.
4. Save -- Render auto-redeploys the service whenever an environment
   variable changes, so this triggers a fresh (empty-database) build
   automatically. No extra button to click.

### 8. Cold-start behavior, plain language

Render's free tier puts your service to sleep after 15 minutes with
no requests. The next request wakes it back up, which takes 30-60
seconds -- so the first page load after any quiet period will hang for
a bit before anything appears. On this free tier, that same wake-up
also means **the app comes back with an empty database**: migrations
re-run automatically (so the schema is correct and the seeded
ingredient/recipe data -- the read-only reference tables baked into
the image -- is present), but any profile, meal log, or unit
calibration you entered before the last sleep is gone. You're
starting fresh every time you come back after a break. That's the
deliberate tradeoff of this tier: it's for looking at the real app on
a real phone, not for logging anything you want to keep.

### 9. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Build fails on the Docker step | Check `Dockerfile` syntax is intact and `requirements.txt` is actually committed to the repo (not just local/gitignored). Read the specific error in the build log -- it names the failing line. |
| `/health` returns a 500 | Check the **Logs** tab for an `alembic upgrade head` traceback near container start -- that's the migration step failing before uvicorn even starts. |
| Service never goes "Live" even though the build succeeded | Render normally auto-detects the port from the Dockerfile's `EXPOSE 7860` line. If it doesn't pick it up, go to **Settings** -> look for a **Port** field and set it to `7860` explicitly, then redeploy. (This auto-detection has occasionally been reported as flaky in Render's community forum -- if `/health` never responds despite a "successful" build, this is the first thing to check.) |
| CORS errors in the browser console | Confirm `CORS_ALLOWED_ORIGINS` matches your Vercel URL **exactly**, including the `https://` prefix and no trailing slash. |
| Magic-link email never arrives | Check the [Resend dashboard](https://resend.com/) for delivery status on that email. If Resend shows nothing at all, check Render's **Logs** tab for an error calling the Resend API (wrong/missing `RESEND_API_KEY` is the usual cause). |
| Service keeps going to sleep and people complain about the wait | That's the free tier working as designed -- see Section 2 below to upgrade. |

---

## Section 2: Starter tier upgrade (~$7.25/month -- future, once the app is validated)

Once you're ready to spend money for a persistent, always-on service
(i.e. once this has proven worth it to family/friends, or you've
decided to hand them this URL for real use instead of the Streamlit
edition), upgrade the **same** web service you already created --
same GitHub repo, same `Dockerfile`, no code changes.

1. Render dashboard -> your `dalgains-api` service -> **Settings** ->
   **Instance Type** -> change from **Free** to **Starter** ->
   confirm. This is where Render will ask for a payment method for
   the first time -- billing starts once you confirm (Starter is
   $7/month at the time of writing; check Render's current pricing
   page since this can change).
2. Still in the service -> **Disks** tab (only visible/usable now
   that the instance is paid) -> **Add Disk**:
   - **Name**: `dalgains-data`
   - **Mount Path**: `/var/data`
   - **Size**: `1 GB` (Render bills disks separately from the
     instance, historically around $0.25/GB/month -- so roughly
     $0.25/month for 1 GB; check the current rate shown in the
     dashboard before confirming, since this figure is worth
     re-verifying at the time you actually do this).
   - Confirm creation.
3. Back in **Environment** -> edit `DATABASE_URL` to point at the new
   disk's mount path instead of the ephemeral one from Section 1:
   ```
   DATABASE_URL=sqlite:////var/data/dalgains.db
   ```
   (Four slashes: `sqlite://` + an absolute path `/var/data/dalgains.db`
   -- easy to typo as three.)
4. Save the env var change -- Render should auto-redeploy, but if it
   doesn't kick off on its own, trigger a manual deploy from the
   **Manual Deploy** button so the new `DATABASE_URL` actually takes
   effect (the running container won't pick up an env var change
   without a restart).
5. **Verify persistence actually works** before trusting it: log a
   test entry through the app, then from the Render dashboard restart
   the service (**Manual Deploy** -> **Restart Service**, or similar,
   depending on the current dashboard layout) and confirm that test
   entry is still there afterward. If it's gone, double-check the
   mount path in both the Disks tab and `DATABASE_URL` match exactly.
6. **Total monthly cost**: roughly **$7.25/month** (~₹600-650 at
   current exchange rates, but check -- this isn't a fixed number)
   for the Starter instance + 1 GB disk. No sleep, no 15-minute
   wake-up delay, and data survives restarts and redeploys.

This is a configuration change on the same web service -- no code
changes needed, same GitHub repo, same `Dockerfile`.
