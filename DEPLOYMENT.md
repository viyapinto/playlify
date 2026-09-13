# Deploying Playlify (Vercel + Render)

Due to the size limitations of Vercel Serverless Functions (AWS Lambda) which cannot bundle the massive PyTorch library along with the model artifacts within its 250MB strict limit, Playlify uses a **split deployment model**:
- **Frontend**: Vercel (Fast, global CDN, perfect for React/Vite)
- **Backend**: Render (Full containerised Python environment, capable of running PyTorch and handling larger models without restrictive timeouts)

## Step 1: Deploy Backend to Render

1. Create a free account on [Render](https://render.com).
2. Connect your GitHub account and click **New+** -> **Blueprint**.
3. Select this `playlify` repository.
4. Render will automatically detect the `render.yaml` file in the root directory and propose deploying the `playlify-backend` Web Service.
5. Click **Apply**.
6. Wait for the deployment to finish (it will take a few minutes to install PyTorch).
7. Copy the URL of your deployed backend (e.g., `https://playlify-backend.onrender.com`).

*Note: Render's free tier spins down after 15 minutes of inactivity. The first request after a period of inactivity may take up to a minute to wake up the server.*

## Step 2: Deploy Frontend to Vercel

1. Create a free account on [Vercel](https://vercel.com).
2. Connect your GitHub account and click **Add New** -> **Project**.
3. Select this `playlify` repository.
4. Vercel should automatically detect it as a **Vite** project.
5. In the **Environment Variables** section, add:
   - **Name**: `VITE_API_URL`
   - **Value**: The Render URL you copied in Step 1 (e.g., `https://playlify-backend.onrender.com`)
6. **Root Directory**: `frontend`
7. Click **Deploy**.
8. Copy your new Vercel URL (e.g., `https://playlify.vercel.app`).

## Step 3: Secure CORS on Render (Optional but Recommended)

Now that you have your Vercel URL, you should restrict your backend to only accept requests from your frontend.

1. Go to your Render Dashboard -> **playlify-backend**.
2. Click **Environment**.
3. Add a new Environment Variable:
   - **Key**: `FRONTEND_URL`
   - **Value**: Your Vercel URL (e.g., `https://playlify.vercel.app`)
4. Save changes (this will trigger a new backend deployment).

## Testing Locally

If you are developing locally, simply run the frontend and backend as usual. The frontend will fallback to `http://127.0.0.1:8000` if `VITE_API_URL` is not set, and the backend will default `FRONTEND_URL` to `http://localhost:5173`.
