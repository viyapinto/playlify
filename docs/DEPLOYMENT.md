# Deploying Playlify (Vercel + Render)

Playlify uses a split deployment model:
- **Frontend**: Vercel (Fast global CDN for React/Vite)
- **Backend**: Render (Containerized Python environment for PyTorch model inference)

---

## Step 1: Deploy Backend to Render

1. Log in to [Render](https://render.com).
2. Click **New +** -> **Web Service** (or select **Blueprint** to auto-configure using `render.yaml`).
3. Connect your GitHub repository `playlify`.
4. Configure the service:
   - **Runtime**: Python 3
   - **Build Command**: `pip install --extra-index-url https://download.pytorch.org/whl/cpu -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variables:
   - `PYTHON_VERSION`: `3.10.12`
   - `FRONTEND_URL`: `*` (update with your Vercel URL after Step 2)
6. Click **Create Web Service** and copy your backend API URL (e.g., `https://playlify-backend.onrender.com`).

---

## Step 2: Deploy Frontend to Vercel

1. Log in to [Vercel](https://vercel.com).
2. Click **Add New** -> **Project** and select the `playlify` repository.
3. Configure project settings:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
4. Add Environment Variable:
   - `VITE_API_URL`: Your Render backend URL from Step 1
5. Click **Deploy** and copy your deployed URL (e.g., `https://playlify.vercel.app`).

---

## Step 3: Secure CORS on Render

Restrict the backend API to accept requests strictly from your Vercel frontend:

1. Go to your Render Dashboard -> **playlify-backend** -> **Environment**.
2. Update `FRONTEND_URL` to your Vercel URL (e.g., `https://playlify.vercel.app`).
3. Save changes.

---

## Local Development Setup

- **Backend**: Navigate to `backend/` and run `uvicorn main:app --reload` (defaults to `http://127.0.0.1:8000`).
- **Frontend**: Navigate to `frontend/` and run `npm run dev` (defaults to `http://localhost:5173`).
