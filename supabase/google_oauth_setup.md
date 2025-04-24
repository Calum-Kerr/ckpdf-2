# Setting Up Google OAuth for RevisePDF

This guide will walk you through setting up Google OAuth for RevisePDF.

## 1. Create a Google OAuth Client

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" and select "OAuth client ID"
5. Select "Web application" as the application type
6. Enter a name for your OAuth client (e.g., "RevisePDF")
7. Add authorized JavaScript origins:
   - For development: `http://localhost:5002`
   - For production: `https://revisepdf.com`
8. Add authorized redirect URIs:
   - For development: `http://127.0.0.1:5002/auth/oauth-callback` (use 127.0.0.1, not localhost)
   - For production: `https://revisepdf.com/auth/oauth-callback`
9. Click "Create"
10. Note your Client ID and Client Secret

## 2. Configure Environment Variables

Add the following environment variables to your application:

```
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

For Heroku deployment, add these environment variables to your Heroku app:

```
heroku config:set GOOGLE_CLIENT_ID=your_client_id
heroku config:set GOOGLE_CLIENT_SECRET=your_client_secret
```

## 2. Configure Supabase Auth Settings

1. Go to your Supabase dashboard
2. Select your project
3. Navigate to "Authentication" > "Providers"
4. Find "Google" in the list of providers and click "Edit"
5. Toggle the "Enabled" switch to on
6. Enter your Google OAuth Client ID and Client Secret
7. Save your changes

## 3. Configure Redirect URLs in Supabase

1. In your Supabase dashboard, go to "Authentication" > "URL Configuration"
2. Set the Site URL to your application URL:
   - For development: `http://localhost:5002`
   - For production: `https://revisepdf.com`
3. Add the following redirect URLs:
   - `http://localhost:5002/auth/oauth-callback` (for development)
   - `https://revisepdf.com/auth/oauth-callback` (for production)
4. Save your changes

## 4. Testing Google OAuth

1. Start your RevisePDF application
2. Go to the login page
3. Click "Sign in with Google"
4. You should be redirected to Google's login page
5. After logging in with your Google account, you should be redirected back to RevisePDF and logged in

## 5. Troubleshooting

### Common Issues:

1. **Redirect URI Mismatch (Error 400: redirect_uri_mismatch)**: Make sure the redirect URI in your Google OAuth client settings exactly matches the one in your application (`http://127.0.0.1:5002/auth/oauth-callback` for development). Note that `127.0.0.1` and `localhost` are considered different by Google OAuth, so be consistent with which one you use.

2. **Missing Environment Variables**: Ensure that you've set the `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` environment variables.

3. **Invalid Client ID or Secret**: Double-check that you've entered the correct Client ID and Secret in your environment variables.

4. **OAuth Callback Not Working**: Make sure your application's OAuth callback route is correctly implemented and matches the redirect URI.

5. **Google API Restrictions**: If you've restricted your Google API, make sure that the OAuth API is enabled for your project.

6. **Consent Screen Not Configured**: Ensure that you've configured the OAuth consent screen in the Google Cloud Console.

### Debugging Tips:

1. Check the browser console for any JavaScript errors
2. Check the application logs for any backend errors
3. Verify that the Google OAuth client is properly configured with the correct redirect URI
4. Try using incognito/private browsing mode to avoid issues with cached credentials
5. Clear your browser cookies and try again if you're experiencing persistent issues
6. Use the Google OAuth Playground to test your OAuth configuration

## 6. Security Considerations

1. Never expose your Google OAuth Client Secret in client-side code
2. Use HTTPS in production to protect user data
3. Implement proper session management to prevent session hijacking
4. Regularly rotate your OAuth client secrets
5. Monitor your application for suspicious login activities
