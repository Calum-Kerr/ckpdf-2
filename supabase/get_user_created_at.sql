-- Function to get a user's creation date from auth.users
-- This function needs to be executed in the Supabase SQL editor
-- It will create a function that can be called from the client

CREATE OR REPLACE FUNCTION public.get_user_created_at(user_id_param UUID)
RETURNS TIMESTAMPTZ
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    created_at_time TIMESTAMPTZ;
BEGIN
    -- Check if the requesting user is the same as the user_id_param
    IF auth.uid() = user_id_param THEN
        -- Get the created_at time from auth.users
        SELECT created_at INTO created_at_time
        FROM auth.users
        WHERE id = user_id_param;
        
        RETURN created_at_time;
    ELSE
        -- If not the same user, return NULL
        RETURN NULL;
    END IF;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION public.get_user_created_at(UUID) TO authenticated;

-- Add a comment to the function
COMMENT ON FUNCTION public.get_user_created_at(UUID) IS 'Gets a user''s creation date from auth.users if the requesting user is the same as the user_id_param';
