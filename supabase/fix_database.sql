-- This script fixes the database schema and RLS policies for the RevisePDF application
-- Run this in the Supabase SQL Editor to fix the profile creation issue

-- First, check if the tables exist and create them if they don't
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

CREATE TABLE IF NOT EXISTS usage_tracking (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    file_size BIGINT NOT NULL,
    operation_type TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create function to update updated_at timestamp if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update updated_at timestamp if it doesn't exist
DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER update_user_profiles_updated_at
BEFORE UPDATE ON user_profiles
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Create index on user_id for faster lookups if they don't exist
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_user_id ON usage_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_created_at ON usage_tracking(created_at);

-- Make sure RLS is enabled on the tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_tracking ENABLE ROW LEVEL SECURITY;

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view their own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can insert their own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can update their own profile" ON user_profiles;
DROP POLICY IF EXISTS "Service role can do anything with user_profiles" ON user_profiles;
DROP POLICY IF EXISTS "Allow profile creation" ON user_profiles;
DROP POLICY IF EXISTS "Server can create profiles for users" ON user_profiles;
DROP POLICY IF EXISTS "Server can update profiles" ON user_profiles;

DROP POLICY IF EXISTS "Users can view their own usage" ON usage_tracking;
DROP POLICY IF EXISTS "Users can insert their own usage" ON usage_tracking;
DROP POLICY IF EXISTS "Service role can do anything with usage_tracking" ON usage_tracking;

-- Create new policies for user_profiles
-- 1. Allow users to view their own profile
CREATE POLICY "Users can view their own profile"
    ON user_profiles FOR SELECT
    USING (auth.uid() = user_id);

-- 2. Allow users to insert their own profile
CREATE POLICY "Users can insert their own profile"
    ON user_profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- 3. Allow users to update their own profile
CREATE POLICY "Users can update their own profile"
    ON user_profiles FOR UPDATE
    USING (auth.uid() = user_id);

-- 4. Allow service role to do anything with user_profiles
CREATE POLICY "Service role can do anything with user_profiles"
    ON user_profiles
    USING (auth.role() = 'service_role');

-- 5. Allow service role to insert any profile (this is the key policy we need)
CREATE POLICY "Service role can insert any profile"
    ON user_profiles FOR INSERT
    WITH CHECK (auth.role() = 'service_role');

-- Create new policies for usage_tracking
-- 1. Allow users to view their own usage
CREATE POLICY "Users can view their own usage"
    ON usage_tracking FOR SELECT
    USING (auth.uid() = user_id);

-- 2. Allow users to insert their own usage
CREATE POLICY "Users can insert their own usage"
    ON usage_tracking FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- 3. Allow service role to do anything with usage_tracking
CREATE POLICY "Service role can do anything with usage_tracking"
    ON usage_tracking
    USING (auth.role() = 'service_role');

-- 4. Allow service role to insert any usage (this is the key policy we need)
CREATE POLICY "Service role can insert any usage"
    ON usage_tracking FOR INSERT
    WITH CHECK (auth.role() = 'service_role');

-- Create a view to check if a user exists in auth.users
CREATE OR REPLACE VIEW public.users AS
SELECT id, email, created_at
FROM auth.users;

-- Create a function to insert a user profile that bypasses RLS
CREATE OR REPLACE FUNCTION insert_user_profile(
    p_user_id UUID,
    p_email TEXT,
    p_account_type TEXT DEFAULT 'free',
    p_storage_used BIGINT DEFAULT 0,
    p_storage_limit BIGINT DEFAULT 52428800,
    p_created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
)
RETURNS SETOF user_profiles
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    INSERT INTO user_profiles (user_id, email, account_type, storage_used, storage_limit, created_at)
    VALUES (p_user_id, p_email, p_account_type, p_storage_used, p_storage_limit, p_created_at)
    RETURNING *;
END;
$$;

-- Grant execute permission on the function to the service role
GRANT EXECUTE ON FUNCTION insert_user_profile TO service_role;

-- Create a function to check if a user exists in auth.users
CREATE OR REPLACE FUNCTION check_user_exists(p_user_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    user_exists BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM auth.users WHERE id = p_user_id) INTO user_exists;
    RETURN user_exists;
END;
$$;

-- Grant execute permission on the function to the service role
GRANT EXECUTE ON FUNCTION check_user_exists TO service_role;
