# Security Documentation

This document provides an overview of the security measures implemented in the RevisePDF application. This information is for internal use only and should not be shared publicly.

## Security Architecture

The RevisePDF application implements a multi-layered security approach:

1. **Input Validation and Sanitisation**
2. **Secure File Processing**
3. **Authentication and Authorisation**
4. **Data Protection**
5. **Server-Side Security**
6. **Client-Side Security**
7. **Monitoring and Logging**

## Security Modules

### File Validation and Sanitisation

- Strict file type validation using magic numbers
- File size limits
- PDF sanitisation to remove potentially harmful elements
- Secure filename generation

### Server Protection

- Resource limits for processing operations
- Timeouts for long-running operations
- Sandboxed execution environment
- Rate limiting for API endpoints

### Data Protection

- Encrypted file storage
- Automatic file deletion after processing
- Secure temporary storage
- Privacy-focused data handling

### Authentication and Authorisation

- CSRF protection
- API token authentication
- Origin checking
- Secure headers

### Security Middleware

- Request logging
- Content type validation
- Request size limits
- Suspicious pattern detection
- Security headers

### Client-Side Security

- Form protection
- Input sanitisation
- Clickjacking prevention
- Basic DevTools protection
- Link protection
- CSP violation reporting

### Security Monitoring

- Suspicious activity detection
- Request rate monitoring
- SQL injection attempt detection
- XSS attempt detection
- Security event logging

## Security Configuration

The application uses the following security configuration:

- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Content-Type-Options: nosniff
- X-Frame-Options: SAMEORIGIN
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Secure cookies with HttpOnly and SameSite flags

## Security Best Practices

When developing new features or making changes to the application, follow these security best practices:

1. **Validate all user inputs** - Never trust user input
2. **Use parameterised queries** - Prevent SQL injection
3. **Sanitise output** - Prevent XSS attacks
4. **Implement proper authentication** - Protect sensitive operations
5. **Use HTTPS** - Encrypt data in transit
6. **Implement proper error handling** - Don't expose sensitive information
7. **Keep dependencies updated** - Prevent known vulnerabilities
8. **Follow the principle of least privilege** - Limit access to resources
9. **Implement proper logging** - Track security events
10. **Conduct regular security reviews** - Identify and fix vulnerabilities

### API Key Management

This project uses Supabase for authentication and database operations. To ensure the security of your application, please follow these additional best practices:

1. **Never commit API keys to the repository**
   - Always use environment variables for sensitive information
   - The `.env` file is included in `.gitignore` to prevent accidental commits

2. **Required Environment Variables**
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_KEY`: Your Supabase anon key (public)
   - `SUPABASE_SERVICE_KEY`: Your Supabase service role key (private)
   - `GOOGLE_CLIENT_ID`: Your Google OAuth client ID
   - `GOOGLE_CLIENT_SECRET`: Your Google OAuth client secret

3. **Service Role Key Security**
   - Only use the service role key on the server side, never in client-side code
   - Only use the service role key when absolutely necessary
   - Regularly rotate the service role key, especially after team member changes

## Security Incident Response

In case of a security incident:

1. **Identify the scope** - Determine what systems are affected
2. **Contain the incident** - Prevent further damage
3. **Eradicate the threat** - Remove the cause of the incident
4. **Recover systems** - Restore normal operations
5. **Learn from the incident** - Improve security measures

## Security Contacts

For security-related issues, contact:

- Lead Developer: calum@revisepdf.com

## Security Updates

This document should be updated whenever significant security changes are made to the application.

Last updated: 2025-05-06
