# Supabase Setup for RevisePDF

This directory contains the necessary files to set up Supabase for RevisePDF authentication and file size tracking.

## Setup Instructions

1. Create a Supabase account at [https://supabase.com](https://supabase.com)
2. Create a new project
3. Go to the SQL Editor in the Supabase dashboard
4. Copy and paste the contents of `schema.sql` into the SQL Editor
5. Run the SQL script to create the necessary tables and policies
6. Go to Project Settings > API to get your Supabase URL and API Key
7. Add the following environment variables to your Heroku app:
   - `SUPABASE_URL`: Your Supabase URL
   - `SUPABASE_KEY`: Your Supabase API Key (use the `anon` key)

## Tables

### user_profiles

This table stores user profile information, including:
- User ID (from Supabase Auth)
- Email
- Account type (free or premium)
- Storage used
- Storage limit
- Created at timestamp
- Updated at timestamp

### usage_tracking

This table tracks file usage, including:
- User ID (from Supabase Auth)
- File size
- Operation type (upload, download, etc.)
- Created at timestamp

## Row Level Security (RLS)

Row Level Security is enabled for both tables to ensure that users can only access their own data.

## Indexes

Indexes are created on the `user_id` column for both tables to improve query performance.

## Triggers

A trigger is created to automatically update the `updated_at` column when a user profile is updated.
