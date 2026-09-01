# LeaseGuard AI

LeaseGuard AI is a 24-hour hackathon project for lease auditing and financial recovery. This Phase 2 setup focuses on the foundation required for Supabase authentication and user ownership.

## Phase 2: Supabase authentication and database foundation

This project uses Supabase for:
- authentication via Email/Password
- user ownership via `auth.users.id`
- future application data storage in a simple PostgreSQL schema

## 1. Create a Supabase project

1. Go to https://supabase.com and create a new project.
2. Choose your organization and project name.
3. Wait for the database to finish provisioning.

## 2. Enable Email authentication

1. In the Supabase dashboard, open Authentication.
2. Click Providers.
3. Enable Email.
4. Save the settings.

## 3. Open the SQL editor

1. In the Supabase dashboard, go to SQL Editor.
2. Open a new query.
3. Copy the contents of `database/schema.sql`.
4. Paste it into the editor.
5. Click Run.

## 4. Create your local environment file

At the project root, create a `.env` file based on `.env.example`.

Example:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-role-key
```

## 5. Install Python dependencies

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 6. Run the Streamlit app

```bash
streamlit run app.py
```

Then open the local URL shown in the terminal, usually:

```text
http://localhost:8501
```

## What Supabase Auth handles

Supabase Auth handles:
- email/password user registration
- login and logout
- session management
- authenticated user identity through `auth.users`
- secure password handling without custom password hashing in our app

## What the SQL schema handles

The SQL schema handles the application-owned data for:
- properties
- documents
- audits
- findings
- risk scores
- recovery records
- disputes

It also keeps each record associated with the correct authenticated user and property.

## How `user_id` connects users to their data

Each application table includes a `user_id` column that references `auth.users(id)`.

This means:
- a user signs in with Supabase Auth
- the authenticated user has a UUID in `auth.users`
- our app uses that ID when creating or querying records
- properties, audits, documents, findings, and recovery-related records remain tied to the logged-in user

Example:

- `auth.users.id = 123e...`
- `properties.user_id = 123e...`
- `documents.user_id = 123e...`
- `audits.user_id = 123e...`

That prevents unrelated users from seeing another user's data.

## How to manually run the SQL

Do this in the Supabase dashboard only:

1. Go to SQL Editor.
2. Create a new query.
3. Paste the full contents of `database/schema.sql`.
4. Run it once.
5. Confirm the tables exist.
6. Keep the SQL as a project artifact for future reference.

Do not use the application to create tables automatically. This project intentionally expects the schema to be created by you in the Supabase dashboard.

## Stop here

This project ends at Phase 2. The next phases would cover deeper lease logic, AI processing, pipeline integration, and more advanced app functionality.
