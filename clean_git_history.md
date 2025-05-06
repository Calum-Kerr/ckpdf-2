# Git History Cleaning Instructions

## IMPORTANT: Security Breach Remediation

A Supabase service role API key was accidentally committed to the Git repository. This is a serious security issue that needs immediate attention.

## Step 1: Rotate Your API Keys (MOST URGENT)

1. Go to your Supabase dashboard: https://app.supabase.com/project/yrmgnrctqnrwjszdtqlq/settings/api
2. Click on "Regenerate" next to the service role key
3. Update your local `.env` file with the new key
4. Update any deployment environments (like Heroku) with the new key

## Step 2: Clean Git History

### Option 1: Using BFG Repo-Cleaner (Recommended)

1. Download BFG Repo-Cleaner from https://rtyley.github.io/bfg-repo-cleaner/
2. Create a file named `passwords.txt` with the following content:
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlybWducmN0cW5yd2pzemR0cWxxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NTI2NzY2OCwiZXhwIjoyMDYwODQzNjY4fQ.OvFLFXfPYIr7FiC-i1benNC4Nc3wS3xIlmO5Efp6zaU
   ```
3. Run the following commands:
   ```bash
   # Clone a fresh copy of your repo
   git clone --mirror https://github.com/Calum-Kerr/ckpdf-2.git ckpdf-2-clean
   cd ckpdf-2-clean
   
   # Run BFG to replace the sensitive data
   java -jar path/to/bfg.jar --replace-text ../passwords.txt
   
   # Clean up and push
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   git push --force
   ```

### Option 2: Using git filter-branch

If you can't use BFG, you can use git filter-branch:

```bash
git filter-branch --force --index-filter \
  "git ls-files -z | xargs -0 sed -i 's/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlybWducmN0cW5yd2pzemR0cWxxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NTI2NzY2OCwiZXhwIjoyMDYwODQzNjY4fQ.OvFLFXfPYIr7FiC-i1benNC4Nc3wS3xIlmO5Efp6zaU/YOUR_PLACEHOLDER_HERE/g'" \
  --prune-empty -- --all
git push origin --force --all
```

## Step 3: Update Your Local Repository

After cleaning the remote repository, update your local repository:

```bash
git fetch --all
git reset --hard origin/master
```

## Step 4: Prevent Future Issues

1. Make sure `.env` is in your `.gitignore` file (it already is)
2. Consider using a pre-commit hook to check for sensitive data
3. Consider using a tool like git-secrets to automatically check for API keys

## Step 5: Verify Security

1. Check that the old API key no longer works
2. Verify that the new API key is working correctly
3. Review your Supabase logs for any unauthorized access

## Additional Security Measures

1. Enable MFA for your Supabase account if available
2. Review all access logs for suspicious activity
3. Consider implementing a secret management solution for production environments
