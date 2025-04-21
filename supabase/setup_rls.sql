-- This script sets up the Row Level Security (RLS) policies for the RevisePDF application
-- Run this in the Supabase SQL Editor to fix the registration issue

-- First, make sure RLS is enabled on the tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_tracking ENABLE ROW LEVEL SECURITY;

-- Create policy to allow users to view their own profile
CREATE POLICY "Users can view their own profile"
    ON user_profiles FOR SELECT
    USING (auth.uid() = user_id);

-- Create policy to allow users to insert their own profile
CREATE POLICY "Users can insert their own profile"
    ON user_profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Create policy to allow users to update their own profile
CREATE POLICY "Users can update their own profile"
    ON user_profiles FOR UPDATE
    USING (auth.uid() = user_id);

-- Create policy to allow users to view their own usage
CREATE POLICY "Users can view their own usage"
    ON usage_tracking FOR SELECT
    USING (auth.uid() = user_id);

-- Create policy to allow users to insert their own usage
CREATE POLICY "Users can insert their own usage"
    ON usage_tracking FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Create service role policies (for admin operations)
CREATE POLICY "Service role can do anything with user_profiles"
    ON user_profiles
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role can do anything with usage_tracking"
    ON usage_tracking
    USING (auth.role() = 'service_role');

-- If you get errors about policies already existing, you can drop them first:
-- DROP POLICY IF EXISTS "Users can view their own profile" ON user_profiles;
-- DROP POLICY IF EXISTS "Users can insert their own profile" ON user_profiles;
-- DROP POLICY IF EXISTS "Users can update their own profile" ON user_profiles;
-- DROP POLICY IF EXISTS "Users can view their own usage" ON usage_tracking;
-- DROP POLICY IF EXISTS "Users can insert their own usage" ON usage_tracking;
-- DROP POLICY IF EXISTS "Service role can do anything with user_profiles" ON user_profiles;
-- DROP POLICY IF EXISTS "Service role can do anything with usage_tracking" ON usage_tracking;
