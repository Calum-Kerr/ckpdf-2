"""
Set up Supabase database schema.
This script sets up the Supabase database schema for the RevisePDF application.
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

def setup_supabase_schema():
    """
    Set up the Supabase database schema.
    
    Returns:
        bool: True if the setup is successful, False otherwise.
    """
    # Load environment variables
    load_dotenv()
    
    # Get Supabase credentials
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    
    # Check if credentials are set
    if not supabase_url or not supabase_key:
        print("Error: Supabase credentials not found in .env file.")
        print("Please set SUPABASE_URL and SUPABASE_KEY in your .env file.")
        return False
    
    # Check if credentials are default values
    if supabase_url == 'your_project_url_here' or supabase_key == 'your_anon_key_here':
        print("Error: Supabase credentials are still set to default values.")
        print("Please update SUPABASE_URL and SUPABASE_KEY in your .env file with your actual credentials.")
        return False
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Read the SQL schema file
        schema_path = os.path.join('supabase', 'schema.sql')
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Execute the SQL schema
        print("Setting up Supabase database schema...")
        
        # Split the SQL into individual statements
        statements = schema_sql.split(';')
        
        # Execute each statement
        for statement in statements:
            # Skip empty statements
            if statement.strip():
                try:
                    # Execute the statement using the REST API
                    # Note: This is a simplified approach and may not work for all SQL statements
                    # For complex schemas, it's better to use the Supabase dashboard SQL editor
                    print(f"Executing SQL statement: {statement[:50]}...")
                    supabase.rpc('exec_sql', {'sql': statement}).execute()
                except Exception as e:
                    print(f"Warning: Error executing SQL statement: {str(e)}")
                    print("This may be normal if the tables already exist.")
        
        print("Supabase database schema setup complete!")
        return True
    except Exception as e:
        print(f"Error setting up Supabase database schema: {str(e)}")
        return False

if __name__ == "__main__":
    success = setup_supabase_schema()
    sys.exit(0 if success else 1)
