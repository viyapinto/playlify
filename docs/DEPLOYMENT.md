# Deploying Playlify (Vercel + Render)

Due to the size limitations of Vercel Serverless Functions (AWS Lambda) which cannot bundle the massive PyTorch library along with the model artifacts within its 250MB strict limit, Playlify uses a **split deployment model**:
- **Frontend**: Vercel (Fast, global CDN, perfect for React/Vite)
- **Backend**: Render (Full containerised Python environment, capable of running PyTorch and handling larger models without restrictive timeouts)

## Step 1: Deploy Backend to Hugging Face Spaces (Recommended Free Option)

Because Vercel Serverless Functions have a 250MB limit, we can't bundle PyTorch there. Hugging Face Spaces is a great alternative that stays awake for 48 hours instead of 15 minutes.

1. Go to [Hugging Face](https://huggingface.co/) and create an account.
2. Click **New Space** in the top right.
3. Enter a Space name (e.g. `playlify-backend`).
4. Select **Docker** as the Space SDK and choose the "Blank" template.
5. Under Space hardware, leave the free CPU basic tier selected.
6. Click **Create Space**.
7. Connect your GitHub repository to Hugging Face, or push your code directly to the space using Git (instructions are provided on the Space creation page).
8. Hugging Face will detect the `Dockerfile` at the root of the repository, build the image, and start the FastAPI server.
9. Click the **"App"** tab in your space. To get your direct API URL, click the three dots (`...`) in the top right of the App window and select **"Embed this Space"**. You will see a "Direct URL" link (it usually looks like `https://username-playlify-backend.hf.space`). Copy this link!

## Step 1 (Alternative): Deploy Backend to Render

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
