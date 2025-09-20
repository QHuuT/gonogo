# GitHub App Setup for Project Integration

## Problem
The current GitHub Actions automation fails to add issues to the GoNoGo project with error:
```
❌ Failed to add to project: Resource not accessible by integration
```

This occurs because the default GITHUB_TOKEN doesn't have permissions for GitHub Projects v2.

## Solution: Create GitHub App

### Step 1: Create GitHub App
1. Go to GitHub Settings → Developer settings → GitHub Apps
2. Click "New GitHub App"
3. Fill out basic information:
   - **Name**: `gonogo-automation`
   - **Homepage URL**: `https://github.com/QHuuT/gonogo`
   - **Webhook**: Uncheck "Active" (we don't need webhooks)

### Step 2: Set Permissions
Configure these permissions:
- **Repository permissions**:
  - Issues: Read and write
  - Metadata: Read
  - Contents: Read
- **Organization permissions**:
  - Projects: Write (this is the key permission we need)

### Step 3: Install App
1. After creating, click "Install App"
2. Install on your account/organization
3. Select repository access (gonogo repo)

### Step 4: Generate Private Key
1. In the app settings, scroll to "Private keys"
2. Click "Generate a private key"
3. Download the .pem file

### Step 5: Configure Repository Secrets
Add these secrets to the gonogo repository:
- `APP_ID`: The GitHub App ID (found in app settings)
- `APP_PRIVATE_KEY`: The content of the .pem file
- `APP_INSTALLATION_ID`: Installation ID (found in app installations)

### Step 6: Update GitHub Actions Workflow
Replace the authentication in the workflow:

```yaml
- name: Generate GitHub App Token
  id: generate_token
  uses: tibdex/github-app-token@v1
  with:
    app_id: ${{ secrets.APP_ID }}
    private_key: ${{ secrets.APP_PRIVATE_KEY }}
    installation_id: ${{ secrets.APP_INSTALLATION_ID }}

- name: Parse epic relationships and automate issue management
  uses: actions/github-script@v7
  with:
    github-token: ${{ steps.generate_token.outputs.token }}
    script: |
      // ... existing script
```

## Alternative: Manual Project Management
If the GitHub App approach is too complex, we can:
1. Remove the project integration from automation
2. Add issues to project manually (which you might prefer anyway)
3. Keep the other automation (assignment, epic linking, label cleanup)

## Recommendation
I recommend Option 1 (GitHub App) because it provides full automation as originally requested in US-00033.