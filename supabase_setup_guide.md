# Supabase Setup Guide for RevisePDF

## Step 1: Create a Supabase Project

1. Go to [Supabase](https://supabase.com/) and sign up or log in
2. Click "New Project" to create a new project
3. Enter a name for your project (e.g., "revisepdf")
4. Set a secure database password (save this somewhere safe)
5. Choose a region closest to your users
6. Click "Create new project"

## Step 2: Get Your API Credentials

1. Once your project is created, go to the project dashboard
2. In the left sidebar, click on "Settings" (gear icon)
3. Click on "API" in the settings menu
4. You'll find your:
   - **Project URL**: This is your `SUPABASE_URL`
   - **anon/public** key: This is your `SUPABASE_KEY`
5. Copy these values to use in the next step

## Step 3: Set Up Database Schema

1. In the left sidebar, click on "SQL Editor"
2. Click "New Query"
3. Copy and paste the entire contents of the `supabase/schema.sql` file
4. Click "Run" to execute the SQL and create the tables

## Step 4: Configure Authentication

1. In the left sidebar, click on "Authentication"
2. Go to "Settings" under Authentication
3. Under "Email Auth", make sure it's enabled
4. You can customize email templates if desired
5. Under "URL Configuration":
   - Set Site URL to your application URL (e.g., http://localhost:5002 for development)
   - Add any additional redirect URLs if needed

## Step 5: Update Your .env File

Update your .env file with the real credentials:

```
# Flask configuration
FLASK_APP=run_app.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key-for-testing

# Supabase configuration
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_anon_key
```

Replace `your_project_url` and `your_anon_key` with the values from Step 2.

## Step 6: Test Your Authentication

1. Run your application
2. Try to register a new user
3. Verify that the user is created in Supabase (check the Authentication > Users section)
4. Test login functionality
5. Test file size limits based on account type
