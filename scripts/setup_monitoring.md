# Setting up uptime monitoring (UptimeRobot)

Step-by-step, meant to be followed manually, after both deploys
(`deploy_hf_spaces.md` and `deploy_vercel.md`) are live. Free tier: 50
monitors, 5-minute check interval, email alerts, no credit card.

## 1. Create an UptimeRobot account

Go to [uptimerobot.com](https://uptimerobot.com/), sign up with just an
email address (no card, no plan selection needed -- the free plan is
the default). Confirm the verification email.

## 2. Add a monitor for the backend

1. Dashboard -> **+ Add New Monitor**.
2. **Monitor Type**: `HTTP(s)`.
3. **Friendly Name**: `DalGains API`.
4. **URL**: your Hugging Face Space's health endpoint, e.g.
   `https://your-username-dalgains-api.hf.space/health` (from
   `deploy_hf_spaces.md` step 8) -- point at `/health`, not the bare
   domain, so a healthy HTTP 200 from a broken container (e.g. one
   that's up but can't reach its database) still gets caught: `/health`
   only returns 200 once the app actually queried the ingredient/recipe
   data, not just "the process is listening."
5. **Monitoring Interval**: `5 minutes` (the shortest interval on the
   free plan).
6. Leave the rest at their defaults and save.

## 3. Add a monitor for the frontend

1. **+ Add New Monitor** again.
2. **Monitor Type**: `HTTP(s)`.
3. **Friendly Name**: `DalGains App`.
4. **URL**: your Vercel deployment's root URL, e.g.
   `https://your-project.vercel.app` (from `deploy_vercel.md` step 5).
5. **Monitoring Interval**: `5 minutes`.
6. Save.

## 4. Set the alert contact

1. Dashboard -> **My Settings** -> **Alert Contacts** (or you'll be
   prompted to add one the first time you save a monitor).
2. Add an **E-mail** contact using your `ADMIN_EMAIL` value (the same
   address configured in the backend's environment variables, per
   `.env.example`) -- so an outage alert reaches the same inbox that
   already gets invite-flow and data-request emails.
3. Confirm the verification email UptimeRobot sends to that address.
4. Edit both monitors from steps 2-3 and make sure this alert contact
   is checked under **Alert Contacts To Notify**.

## 5. What a working setup looks like

- Dashboard shows both monitors as **Up** (green) within a few minutes
  of creation, with a response time graph starting to fill in.
- Pausing either service (e.g. restarting the HF Space) should flip its
  monitor to **Down** (red) within one 5-minute check cycle and send an
  email to `ADMIN_EMAIL` -- worth doing once deliberately, right after
  setup, to confirm the alert email actually arrives rather than
  discovering a misconfigured contact during a real outage.
- UptimeRobot's public status-page feature (Dashboard -> **Status
  Pages**) is optional and not needed for this setup -- alerting to
  `ADMIN_EMAIL` is the only requirement here.

---

**Session note**: same as `deploy_hf_spaces.md` and
`deploy_vercel.md` -- this session doesn't have your UptimeRobot
credentials and can't click through this UI on your behalf. This doc is
the part prepared in advance; steps 1-5 are yours to run, after both
services are actually live at real URLs.
