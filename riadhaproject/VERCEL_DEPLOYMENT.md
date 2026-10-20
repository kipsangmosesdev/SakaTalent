# Deploying SakaTalent to Vercel

Vercel can run this Django project, but production needs persistent services. Local SQLite and the `media/` folder remain the development defaults; Vercel function storage is ephemeral.

## 1. Create the Vercel project

Import the Git repository into Vercel and set **Root Directory** to `riadhaproject` (the directory containing `manage.py` and `requirements.txt`). Vercel detects Django projects from `manage.py`, so this project does not need a custom `vercel.json` build configuration.

## 2. Configure PostgreSQL

Create a managed PostgreSQL database and add its connection string to Vercel as `DATABASE_URL`. Add it to Production, Preview, and Development only when each environment has an appropriate database. The app uses `DATABASE_URL` when present and local SQLite otherwise. Production PostgreSQL connections require SSL.

After setting the production environment variable, apply Django migrations to that database. One option is to pull the Vercel environment locally, then run the migration from this project directory:

```powershell
vercel env pull .env.vercel.production
$env:DJANGO_SECRET_KEY = "your-production-secret"
Get-Content .env.vercel.production | ForEach-Object {
    if ($_ -match '^([^#=]+)=(.*)$') { Set-Item -Path "Env:$($matches[1])" -Value $matches[2].Trim('"') }
}
python manage.py migrate
```

Do not commit the downloaded environment file. Verify that `DATABASE_URL` points to the intended database before running migrations. Existing SQLite records are not copied automatically; export/import them separately if they need to appear in production.

## 3. Configure persistent uploads

Create a private S3-compatible bucket (for example, in Supabase Storage) and set these Vercel environment variables:

- `AWS_STORAGE_BUCKET_NAME`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_S3_ENDPOINT_URL`
- `AWS_S3_REGION_NAME` (use the region provided for S3 access)

The app issues time-limited signed URLs for uploaded files. Keep the bucket private because athlete profiles and supporting documents may contain personal information. With no storage variables set, local development continues to save files under `media/`.

## 4. Set Django production variables

Set a unique `DJANGO_SECRET_KEY` in Vercel and set `DJANGO_DEBUG=False`. Vercel supplies deployment host names, which Django adds to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`. For a custom domain, also add its hostname to `DJANGO_ALLOWED_HOSTS` and its HTTPS origin to `DJANGO_CSRF_TRUSTED_ORIGINS`.

To enable Google sign-in, create a **Web application** OAuth client in Google Cloud Console. Add this exact authorized redirect URI:

```text
https://sakatalent.vercel.app/signup/google/callback/
```

In Vercel, add `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` to the **Production** environment. Set `GOOGLE_REDIRECT_URI` to the URI above. Keep the client secret in Vercel only; never commit it. Redeploy after saving these variables. The same Google button handles both login and signup: verified existing email addresses are signed in, while new addresses get an account and are sent to profile setup.

Add production email settings if the app needs them.

## 5. Deploy and verify

Deploy after setting the environment variables. Vercel's Django integration handles the app and static assets. Confirm that the home page loads, sign-in works, and an uploaded file can be retrieved. Existing uploads are not copied automatically.

Vercel's Hobby plan is limited to personal, non-commercial use. Check the current plan terms and the database and storage providers' limits before using the deployment for a public or commercial service.
