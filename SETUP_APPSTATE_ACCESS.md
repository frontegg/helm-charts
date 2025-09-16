# AppState Access Setup with GitHub App

## Problem
The microservices version sync workflow needs access to the private `frontegg/AppState` repository to query production versions. The default `secrets.GITHUB_TOKEN` provided by GitHub Actions **cannot access other repositories**, especially private ones.

## Solution
We use a **GitHub App** for authentication, which is more secure and provides fine-grained permissions compared to Personal Access Tokens (PATs).

## Step-by-Step Setup

### 1. Create a GitHub App

1. Go to GitHub Organization Settings: https://github.com/organizations/frontegg/settings/apps
2. Click **"New GitHub App"**
3. Configure the app:
   - **GitHub App name**: `helm-charts-appstate-access`
   - **Description**: `Access to AppState repository for microservices version sync`
   - **Homepage URL**: `https://github.com/frontegg/helm-charts`
   - **Webhook**: Uncheck "Active" (we don't need webhooks)

### 2. Set Repository Permissions

In the **Repository permissions** section:
- **Contents**: `Read` (to read AppState files)
- **Actions**: `Write` (to trigger workflows in terraform-private-env)
- **Metadata**: `Read` (required by GitHub)

### 3. Install the App

1. After creating the app, go to **Install App** tab
2. Click **"Install"** next to your organization
3. Select **"Only select repositories"**
4. Choose:
   - ✅ `frontegg/AppState`
   - ✅ `frontegg/terraform-private-env`
5. Click **"Install"**

### 4. Generate and Add Private Key

1. In your GitHub App settings, scroll to **Private keys**
2. Click **"Generate a private key"**
3. Download the `.pem` file
4. Go to your helm-charts repository settings
5. Navigate to **Settings** → **Secrets and variables** → **Actions**
6. Add two secrets:
   - **Name**: `APPSTATE_APP_ID`
   - **Secret**: Your GitHub App ID (found in app settings)
   - **Name**: `APPSTATE_APP_PRIVATE_KEY`
   - **Secret**: Contents of the `.pem` file (copy entire file including headers)

### 5. Test the Setup

Run the workflow manually to test:
1. Go to **Actions** tab in your repository
2. Select **"OnPrem Update Charts - Microservices Version Sync"**
3. Click **"Run workflow"**
4. Enable **"Run in dry-run mode"** for testing
5. Click **"Run workflow"**

## Troubleshooting

### Error: "Repository frontegg/AppState not found or not accessible"
- ✅ Verify the GitHub App is installed on the `frontegg/AppState` repository
- ✅ Check that the App ID and private key are correct
- ✅ Ensure the app has `Contents: Read` permission
- ✅ Confirm the secret names are exactly `APPSTATE_APP_ID` and `APPSTATE_APP_PRIVATE_KEY`

### Error: "Authentication failed"
- ✅ Private key may be malformed (ensure entire .pem file is copied)
- ✅ App ID may be incorrect
- ✅ Check if the GitHub App still exists and is active

### Error: "Access forbidden"
- ✅ GitHub App may not be installed on the target repository
- ✅ App permissions may be insufficient
- ✅ Repository may require specific app installation approval

## Security Notes

- 🔒 **Keep the private key secure** - never commit it to code
- 🔒 **Use minimal required permissions** - only `Contents: Read` and `Actions: Write`
- 🔒 **Rotate private keys regularly** - GitHub Apps support key rotation
- 🔒 **Monitor app usage** - GitHub provides installation and usage logs
- 🔒 **Limit repository access** - only install on required repositories

## GitHub App Permissions Required

| Repository | Permission | Reason |
|------------|------------|---------|
| `frontegg/AppState` | Contents: Read | Query production versions from `applications/*/production-global/values.yaml` |
| `frontegg/terraform-private-env` | Actions: Write | Trigger "Create Customer Environment" workflow |
| `frontegg/helm-charts` | N/A | Uses default `GITHUB_TOKEN` for local operations |

## Workflow Configuration

The workflow uses GitHub App authentication for external repositories:

```yaml
# Generate GitHub App token for external repository access
- name: Generate GitHub App Token
  id: app-token
  uses: actions/create-github-app-token@v1
  with:
    app-id: ${{ secrets.APPSTATE_APP_ID }}
    private-key: ${{ secrets.APPSTATE_APP_PRIVATE_KEY }}
    owner: frontegg
    repositories: AppState,terraform-private-env

# Use the generated token for external operations
env:
  GITHUB_TOKEN: ${{ steps.app-token.outputs.token }}

# Local repository operations still use default token
with:
  token: ${{ secrets.GITHUB_TOKEN }}
```

## Advantages of GitHub Apps over PATs

- ✅ **Fine-grained permissions** - only the permissions you need
- ✅ **Repository-scoped** - access only to specific repositories
- ✅ **Organization-managed** - centralized control and auditing
- ✅ **No user dependency** - not tied to a specific user account
- ✅ **Better security** - shorter-lived tokens, automatic rotation
- ✅ **Rate limits** - higher API rate limits than PATs
