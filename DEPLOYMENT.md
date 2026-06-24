# Deployment Guide

This project is configured for deployment on **Vercel** as a Python Flask web application.

## Required Environment Variables

Set the following environment variables in Vercel (**Project Settings -> Environment Variables**):

```text
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=mixtral-8x7b-32768
SECRET_KEY=use_a_long_random_secret_value
```

### Optional Environment Variables

```text
NUM_QUIZ_QUESTIONS=5
MAX_UPLOAD_MB=500
```

> [!IMPORTANT]
> `GROQ_API_KEY` is strongly recommended for Vercel deployment. Without it, the app attempts to fall back to local models (`faster-whisper` and Hugging Face `transformers` summarizer), which are too heavy for Vercel's serverless container environment and will exceed function memory and execution time limits.

---

## Vercel Serverless Function Execution details

This app is configured to detect when it is running on Vercel (using the environment variable `VERCEL=1`). 

- **Local Execution:** Processing runs asynchronously in a background thread so the user sees a live progress bar.
- **Vercel Deployment:** The application automatically runs the video pipeline **synchronously** inside the `/upload` request. This prevents the serverless container from suspending or terminating before the transcription, summarization, and quiz generation are completed.
- **Function Timeout:** Ensure that your Vercel Function timeout (configured via `vercel.json` or project settings) is set high enough to accommodate the synchronous processing (Hobby plan limit is 10s; Pro plans support up to 300s/900s). For Hobby plans, upload only short video clips.

---

## How to Deploy to Vercel

### Option 1: Via Vercel CLI (Recommended for command line)

1. Open a terminal in the root of the project directory.
2. Run the deployment command:
   ```bash
   vercel
   ```
3. Follow the CLI prompts to link and deploy your project.
4. Set the environment variables when prompted or in the Vercel Dashboard under project settings.
5. Deploy to production by running:
   ```bash
   vercel --prod
   ```

### Option 2: Via GitHub Integration (Continuous Deployment)

1. Push your repository to GitHub.
2. Go to the [Vercel Dashboard](https://vercel.com) and click **Add New -> Project**.
3. Import your GitHub repository.
4. Expand **Environment Variables** and add:
   - `GROQ_API_KEY`
   - `GROQ_MODEL`
   - `SECRET_KEY`
5. Click **Deploy**. Vercel will automatically build and deploy the app using the configurations in `vercel.json`.
