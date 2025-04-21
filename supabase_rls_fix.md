# Fixing Row Level Security in Supabase

The registration is failing because of a Row Level Security (RLS) policy issue. We need to add a policy to allow users to insert their own profile.

## Option 1: Run the SQL in the Supabase Dashboard

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

## Option 2: Run the Full Schema

If you prefer to set up the entire schema from scratch:

1. Log in to your Supabase dashboard
2. Go to the SQL Editor
3. Create a new query
4. Paste the entire contents of the `supabase/schema.sql` file
5. Click "Run" to execute the SQL

## After Running the SQL

After running the SQL, try registering a user again. The registration should now work correctly.

If you still encounter issues, check the Supabase logs in the dashboard for more details.
