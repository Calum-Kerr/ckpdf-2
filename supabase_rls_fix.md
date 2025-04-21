# Complete Supabase Setup Guide for RevisePDF

## 1. Fix Row Level Security (RLS) Policies

The registration is failing because of a Row Level Security (RLS) policy issue. We need to add a policy to allow users to insert their own profile.

### Option 1: Run the SQL in the Supabase Dashboard

1. Log in to your Supabase dashboard
2. Go to the SQL Editor
3. Create a new query
4. Paste the following SQL:

```sql
-- Add policy to allow users to insert their own profile
CREATE POLICY "Users can insert their own profile"
    ON user_profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);
```

5. Click "Run" to execute the SQL

### Option 2: Run the Full Schema

If you prefer to set up the entire schema from scratch:

1. Log in to your Supabase dashboard
2. Go to the SQL Editor
3. Create a new query
4. Paste the entire contents of the `supabase/schema.sql` file
5. Click "Run" to execute the SQL

## 2. Configure Authentication Settings

1. In your Supabase dashboard, go to Authentication > Settings
2. Under "Site URL", enter your application URL (e.g., http://localhost:5002 for development)
3. Under "Redirect URLs", add the following URLs:
   - http://localhost:5002/auth/callback
   - http://localhost:5002/auth/dashboard
   - http://localhost:5002/
4. Under "Email Templates", customize the templates if desired
5. Save your changes

## 3. Enable Email Confirmation (Optional)

By default, Supabase requires email confirmation. You can disable this for development:

1. Go to Authentication > Settings
2. Under "Email Auth", toggle off "Enable email confirmations"
3. Save your changes

## 4. Create a Service Role Key (For Admin Functions)

If you need to perform admin functions:

1. Go to Settings > API
2. Find the "service_role" key (keep this secret!)
3. You can use this key for admin operations, but never expose it in client-side code

## 5. Test the Authentication System

After making these changes:

1. Restart your application
2. Try registering a new user
3. Check the Supabase dashboard under Authentication > Users to see if the user was created
4. Try logging in with the new user
5. Check the user_profiles table in the Database section to see if a profile was created

## Troubleshooting

If you still encounter issues:

1. Check the application logs for specific error messages
2. Check the Supabase logs in the dashboard (Settings > Logs)
3. Verify that your .env file has the correct Supabase URL and API key
4. Make sure you're using the anon/public key for client-side operations, not the service_role key
5. Check that the RLS policies are correctly set up (Database > Tables > user_profiles > Policies)

## Next Steps

Once authentication is working:

1. Implement file size limits based on account type
2. Add Stripe integration for premium subscriptions
3. Create subscription management pages
4. Implement upgrade/downgrade functionality
