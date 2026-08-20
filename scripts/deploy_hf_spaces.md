# Deploying the backend to Hugging Face Spaces

> **DEPRECATED (August 2026)** -- Hugging Face Spaces changed their
> pricing: Docker Spaces now require a paid PRO plan ($9/mo). This
> deployment path is no longer viable for a free deployment. For
> current deployment options see `scripts/deploy_render.md` (React
> edition) or `scripts/deploy_streamlit.md` (Streamlit edition, added
> later).

Step-by-step, meant to be followed manually. Free CPU tier, no credit
card, no sleeping, persistent storage via the Space's own `/data`
volume, direct `git push` deploys.

## 1. Create a Hugging Face account

Go to [huggingface.co/join](https://huggingface.co/join). Free, no
credit card -- just an email you verify.

## 2. Create the Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space).
2. **Owner**: your account. **Space name**: e.g. `dalgains-api`.
3. **License**: AGPL-3.0 (matches this repo's `LICENSE`).
4. **Select the Space SDK**: **Docker** (not Gradio/Streamlit -- this
   repo's root `Dockerfile` is a plain FastAPI backend, not a
   Gradio/Streamlit app).
5. **Space hardware**: the free CPU basic tier.
6. **Visibility**: **Public**. This is required for the free tier
   (private Spaces need a paid plan) -- fine here, since this repo is
   AGPL-3.0 and meant to be publicly readable anyway.
7. Click **Create Space**.

You'll land on an empty Space with its own git remote URL, shown on
the page: `https://huggingface.co/spaces/{your-username}/{space-name}`.

## 3. Get an access token

1. Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
2. **Create new token** -> type **Write** (needed to `git push` to the
   Space) -> name it something like `dalgains-deploy`.
3. Copy the token now -- you won't be able to see it again. You'll use
   it as the password when `git push` prompts for credentials (username
   is your HF username).

## 4. Add the Space as a git remote

From this repo's root, on your machine (not this session -- see note
at the end):

```bash
git remote add hf https://huggingface.co/spaces/{your-username}/{space-name}
```

## 5. Push to deploy

HF Spaces builds directly from what you push -- there's no separate
"deploy" step.

```bash
git push hf claude/dalgains-phase-5-deploy:main
```

(Pushing this phase's branch to the Space's `main` -- HF Spaces always
builds from `main`, regardless of what your own repo calls its default
branch. Once this phase is merged into this repo's own `main`, later
deploys are just `git push hf main:main`.)

When prompted for credentials: username is your HF username, password
is the access token from step 3.

**What a successful deploy looks like**: the Space page shows a
"Building" status with a spinner, then switches to "Running" (green)
once the Docker image finishes building and the container starts
serving traffic. This repo's `Dockerfile` runs `alembic upgrade head`
before `uvicorn` starts (see the `CMD` line) -- if that migration step
fails, the container exits immediately and the Space shows "Runtime
error" instead of "Running", with the actual error in the build logs
(see below).

## 6. How to read the build logs

On the Space page, click the **Logs** tab. There are two sub-tabs:
- **Build logs**: the Docker image build itself (pip install, apt-get,
  COPY steps). A failure here means something in `Dockerfile` or
  `requirements.txt` is broken.
- **Container logs**: what the running container prints, including the
  `alembic upgrade head` output and uvicorn's own startup/request logs.
  A failure here (e.g. `FATAL: invalid configuration` from
  `src/config.py`) usually means a required environment variable is
  missing -- see step 7.

## 7. Set environment variables

Space page -> **Settings** tab -> **Variables and secrets**. Add every
variable from this repo's `.env.example`, with these production-specific
values:

| Variable | Value |
|---|---|
| `DATABASE_URL` | `sqlite:////data/dalgains.db` (note: **four** slashes -- three for the `sqlite://` scheme, one for the absolute path `/data/...`. HF Spaces' Docker SDK mounts a persistent volume at `/data`, so this survives container restarts.) |
| `JWT_SECRET` | Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"` -- mark as **secret**. |
| `RESEND_API_KEY` | From [resend.com/api-keys](https://resend.com/api-keys) (see the main repo README / `.env.example` for the free-tier details) -- mark as **secret**. |
| `APP_URL` | Your Vercel frontend URL once step F is done, e.g. `https://dalgains.vercel.app`. You can leave this as the `.env.example` default for now and come back to update it after deploying the frontend. |
| `ADMIN_EMAIL` | Your own email -- auto-invited (and made admin) the first time the Space boots with this set. |
| `ENVIRONMENT` | `prod` -- this is what makes `src/config.py` enforce the fail-fast checks above (missing `JWT_SECRET`/`RESEND_API_KEY`/`CORS_ALLOWED_ORIGINS` will refuse to boot rather than silently misbehave). |
| `CORS_ALLOWED_ORIGINS` | Your Vercel frontend URL, e.g. `https://dalgains.vercel.app` (no trailing slash, comma-separate if you have more than one, e.g. a preview URL too). |

Mark `JWT_SECRET` and `RESEND_API_KEY` as **secret** (the toggle next
to each variable) -- the rest can stay as plain variables since they're
not sensitive on their own.

Setting a variable triggers an automatic rebuild+restart -- watch the
Logs tab again after saving.

## 8. Verify it's running

Once the Space shows "Running":

```bash
curl https://{your-username}-{space-name}.hf.space/health
```

Expected: `{"status":"ok","ingredient_count":...,"recipe_count":8,"version":"0.4.0"}`

**Note this URL** -- it's `VITE_API_URL` for the Vercel frontend deploy
(`scripts/deploy_vercel.md`, step 4) and `Access-Control-Allow-Origin`
needs your Vercel URL added to `CORS_ALLOWED_ORIGINS` above once you
have it.

## If a migration fails

If `alembic upgrade head` fails on startup (visible in Container logs),
the container exits and the Space shows "Runtime error" rather than
silently running on a stale schema. To recover:
1. Fix whatever the log says (usually a migration file issue, or
   `DATABASE_URL` pointing somewhere unwritable).
2. Push a fix, or just click **Restart this Space** (Space page,
   top-right "..." menu) once the underlying issue is resolved --
   restarting re-runs the full `CMD` (migration then uvicorn), it
   doesn't reuse a half-started process.

## Restarting the Space manually

Space page -> top-right "..." menu -> **Restart this Space**. Useful
after changing an env var that doesn't trigger an auto-rebuild, or to
recover from a stuck state.

---

**Session note**: this deploy session (Claude Code) doesn't have your
Hugging Face credentials and can't push to a Space on your behalf --
these steps are written for you to run yourself, from your own machine
with your own git and HF login. The `Dockerfile`, `.dockerignore`, and
this doc are the parts of the work that could be prepared in advance;
steps 1-3 and the actual `git push hf ...` are yours to run.
