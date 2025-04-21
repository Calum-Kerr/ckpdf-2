# Complete Supabase Authentication Setup Guide for RevisePDF

This guide will walk you through setting up Supabase authentication for RevisePDF, including handling common issues and troubleshooting.

## 1. Supabase Project Setup

### Create a Supabase Project
1. Go to [Supabase](https://supabase.com/) and sign up or log in
2. Click "New Project" to create a new project
3. Enter a name for your project (e.g., "revisepdf")
4. Set a secure database password (save this somewhere safe)
5. Choose a region closest to your users
6. Click "Create new project"

### Get Your API Credentials
1. Once your project is created, go to the project dashboard
2. In the left sidebar, click on "Settings" (gear icon)
3. Click on "API" in the settings menu
4. You'll find your:
   - **Project URL**: This is your `SUPABASE_URL`
   - **anon/public** key: This is your `SUPABASE_KEY`
5. Copy these values to your `.env` file

## 2. Database Schema Setup

### Option 1: Run the SQL Script
1. In your Supabase dashboard, go to the SQL Editor
2. Create a new query
3. Paste the contents of the `supabase/setup_rls.sql` file
4. Click "Run" to execute the SQL

### Option 2: Manual Setup
If you prefer to set up the schema manually:

1. Create the `user_profiles` table:
```sql
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    account_type TEXT NOT NULL DEFAULT 'free',
    storage_used BIGINT NOT NULL DEFAULT 0,
    storage_limit BIGINT NOT NULL DEFAULT 52428800, -- 50MB in bytes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

2. Create the `usage_tracking` table:
```sql
CREATE TABLE IF NOT EXISTS usage_tracking (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    file_size BIGINT NOT NULL,
    operation_type TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

3. Set up Row Level Security (RLS) policies:
```sql
-- Enable RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_tracking ENABLE ROW LEVEL SECURITY;

-- Create policies for user_profiles
CREATE POLICY "Users can view their own profile"
    ON user_profiles FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own profile"
    ON user_profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own profile"
    ON user_profiles FOR UPDATE
    USING (auth.uid() = user_id);

-- Create policies for usage_tracking
CREATE POLICY "Users can view their own usage"
    ON usage_tracking FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own usage"
    ON usage_tracking FOR INSERT
    WITH CHECK (auth.uid() = user_id);
```

## 3. Configure Authentication Settings

### Email Confirmation Settings
By default, Supabase requires email confirmation. For development, you may want to disable this:

1. Go to Authentication > Settings
2. Under "Email Auth", toggle off "Enable email confirmations"
3. Save your changes

### URL Configuration
1. Under "URL Configuration":
   - Set Site URL to your application URL (e.g., http://localhost:5002 for development)
   - Add any additional redirect URLs if needed:
     - http://localhost:5002/auth/callback
     - http://localhost:5002/auth/dashboard
     - http://localhost:5002/

### Email Templates (Optional)
1. Under "Email Templates", you can customize the templates for:
   - Confirmation emails
   - Invitation emails
   - Magic link emails
   - Reset password emails

## 4. Troubleshooting Common Issues

### Issue: "The CSRF session token is missing"
This happens when a form is submitted without a valid CSRF token.

**Solution**: Make sure your form includes `{{ form.hidden_tag() }}` and does not have duplicate CSRF token fields.

### Issue: "new row violates row-level security policy for table 'user_profiles'"
This happens when a user tries to insert a row into the `user_profiles` table but doesn't have permission.

**Solution**: Make sure you have the correct RLS policy:
```sql
CREATE POLICY "Users can insert their own profile"
    ON user_profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);
```

### Issue: "Invalid login credentials" during registration
This happens when trying to log in immediately after registration when email confirmation is required.

**Solution**:
1. Either disable email confirmation in Supabase settings, or
2. Update your registration flow to handle unverified users (as we've done in the code)

### Issue: "policy already exists"
This happens when trying to create an RLS policy that already exists.

**Solution**: Use `DROP POLICY IF EXISTS` before creating the policy:
```sql
DROP POLICY IF EXISTS "Users can insert their own profile" ON user_profiles;
CREATE POLICY "Users can insert their own profile"
    ON user_profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);
```

## 5. Testing Your Authentication System

1. Register a new user
2. If email confirmation is enabled:
   - Check your email for the confirmation link
   - Click the link to confirm your account
3. Log in with your credentials
4. Check the Supabase dashboard:
   - Under Authentication > Users to see if the user was created
   - Under Database > Tables > user_profiles to see if a profile was created

## 6. Next Steps

Once authentication is working:

1. Implement file size limits based on account type
2. Add Stripe integration for premium subscriptions
3. Create subscription management pages
4. Implement upgrade/downgrade functionality

## 7. Useful Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Row Level Security Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [Flask-WTF Documentation](https://flask-wtf.readthedocs.io/en/1.0.x/)
