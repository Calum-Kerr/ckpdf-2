-- This script fixes the Row Level Security (RLS) policies for the RevisePDF application
-- Run this in the Supabase SQL Editor to fix the profile creation issue

-- First, drop the existing policies
DROP POLICY IF EXISTS "Users can insert their own profile" ON user_profiles;
DROP POLICY IF EXISTS "Service role can do anything with user_profiles" ON user_profiles;

-- Create a more permissive policy for inserting profiles
CREATE POLICY "Allow profile creation"
    ON user_profiles FOR INSERT
    WITH CHECK (true);  -- Allow any authenticated user to create a profile

-- Create a policy for the service role
CREATE POLICY "Service role can do anything with user_profiles"
    ON user_profiles FOR ALL
    USING (auth.role() = 'service_role');

-- Create a policy to allow the server to create profiles for users
CREATE POLICY "Server can create profiles for users"
    ON user_profiles FOR INSERT
    WITH CHECK (true);

-- Create a policy to allow the server to update profiles
CREATE POLICY "Server can update profiles"
    ON user_profiles FOR UPDATE
    USING (true);
