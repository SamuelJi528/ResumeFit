# Deploy the website

The app serves its frontend and API from one Python service. Your computer can be turned off after it is deployed.

## Render setup

1. Upload the contents of this project folder to a GitHub repository. Keep `server.py`, `requirements.txt`, and `render.yaml` at the repository root. Include `static/`, `templates/`, and `samples/`.
2. Sign in to [Render](https://dashboard.render.com/), choose **New -> Web Service**, and connect that repository.
3. Use Python 3 with build command `pip install -r requirements.txt`.
4. Set the start command to:

```bash
gunicorn server:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 300
```

5. Add environment variables: `GEMINI_API_KEY` with your real key, `GEMINI_MODEL=gemini-3.5-flash-lite`, and `TRUST_PROXY=1`. Set `SITE_ACCESS_CODE` to a shared class-demo code if you want restricted access.
6. Choose the available hosting plan, deploy, then open the resulting URL. Test a review, refinement, and download with your actual API project.

You can instead use **New -> Blueprint** and select the included `render.yaml`. Review its settings and provide the secret values when prompted.

Render's [Flask deployment guide](https://render.com/docs/deploy-flask) documents this setup. Its [free-service limits](https://render.com/docs/free) currently include spinning down after 15 minutes without traffic; waking can take about a minute. Open and test the site before presenting. Check current plan availability/pricing in your account.

## Docker or another Python host

```bash
docker build -t resumefit .
docker run --env-file .env -p 8000:8000 resumefit
```

Open `http://localhost:8000`. The image uses Gunicorn, reads the host's `PORT` when supplied, and excludes `.env` from the image. The Docker path has not been built in the development environment; verify it on a Docker-enabled machine.

For another host, use the same build/start commands and environment variables. Keep `TRUST_PROXY=0` unless that host uses one trusted reverse proxy and its documentation supports the setting. A real public deployment should use the host's HTTPS URL.

## API key and usage

Google AI Pro's Studio benefits do not automatically pay for this external website's API calls. Check the API project's model access, quota, and billing in AI Studio.

The backend keeps the key out of browser assets and responses. Public visitors can still consume the server's API quota by generating reviews. Use the included demo access code and request limits for a class presentation. Limits are per process, reset on restart, and permit up to two Gemini calls per generation attempt; they are not a provider billing cap.

The app has no resume database or user accounts. If expanding to sustained public use, add stronger abuse protection, shared rate-limit storage, and an appropriate data policy.

## Verify after deployment

- Open `/api/health`: it should return `status: ok` and `ready: true`.
- Load the sample and generate a real review.
- Refine a bullet and download the report.
- Check mobile layout and keyboard navigation.
- Confirm the repository and public browser files contain no real API key.
- Keep the deployed URL for the assignment's optional publishing bonus.
