# Deployment Guide: ERPNext Xero App on Frappe Cloud

This guide walks you through deploying and testing the ERPNext Xero Integration app on **Frappe Cloud**.

---

## Prerequisites

- ✅ Frappe Cloud account (trial or paid)
- ✅ ERPNext site created on Frappe Cloud
- ✅ Xero Developer account with an app created
- ✅ Git repository (GitHub/GitLab) - recommended, or SSH access if you have Private Bench

---

## Step 1: Get Your ERPNext API Credentials

1. **Log into your ERPNext site** (e.g., `your-site.frappe.cloud`)
2. Go to **Settings** → **Users** → **API Access**
3. Click **Generate Keys** (or use existing keys)
4. **Copy and save**:
   - **API Key**
   - **API Secret**

   > ⚠️ **Important**: Keep these secure. You'll need them for the sync engine.

---

## Step 2: Prepare Your Xero App

1. Go to **https://developer.xero.com/myapps**
2. Create a new app (or use existing):
   - **App Name**: `ERPNext Integration`
   - **Redirect URI**: 
     ```
     https://your-site.frappe.cloud/api/method/erpnext_xero_app.xero_integration.api.xero_oauth_callback
     ```
     > ⚠️ Replace `your-site.frappe.cloud` with your actual Frappe Cloud site URL
3. **Note down**:
   - **Client ID**
   - **Client Secret**

---

## Step 3: Deploy the App to Frappe Cloud

### Option A: Using Git (Recommended)

**If you have Private Bench or can push to GitHub:**

1. **Push the app to GitHub**:
   ```bash
   cd /path/to/Odoo_scope_automations/ERPNext/erpnext_xero_app
   git init
   git add .
   git commit -m "Initial commit: ERPNext Xero Integration app"
   git remote add origin https://github.com/your-username/erpnext-xero-app.git
   git push -u origin main
   ```

2. **In Frappe Cloud Dashboard**:
   - Go to your site → **Apps** → **Deploy App**
   - Enter your GitHub repo URL: `https://github.com/your-username/erpnext-xero-app`
   - Click **Deploy**
   - Frappe Cloud will automatically install it

3. **Run migrations**:
   - In Frappe Cloud dashboard → **Console** → Run:
     ```bash
     bench --site your-site.local migrate
     ```

### Option B: Using SSH (Private Bench Only)

**If you have Private Bench with SSH access:**

1. **SSH into your Frappe Cloud site**:
   ```bash
   ssh your-site@frappecloud.com
   ```

2. **Navigate to apps directory**:
   ```bash
   cd ~/apps
   ```

3. **Upload the app** (using `scp` from your local machine):
   ```bash
   # From your local machine:
   scp -r erpnext_xero_app your-site@frappecloud.com:~/apps/
   ```

4. **Install the app**:
   ```bash
   bench --site your-site.local install-app erpnext_xero_app
   bench --site your-site.local migrate
   ```

### Option C: Manual File Upload (Limited - Not Recommended)

**If you only have shared hosting:**

- Frappe Cloud shared hosting doesn't allow direct file uploads for apps
- You'll need to upgrade to **Private Bench** ($25+/mo) to install custom apps
- Or use Option A (Git deployment) if available

---

## Step 4: Configure inside ERPNext (no env vars needed)

This app stores all credentials and tokens in the **`Xero Settings`** DocType (encrypted password fields).  
You do **not** need environment variables.

After installing the app:

1. Open **Xero Settings**
2. Enter **Client ID**, **Client Secret**, **Redirect URI**
3. Click **Connect to Xero**
4. Click **Test Connection**

---

## Step 5: Test the App in ERPNext UI

1. **Log into your ERPNext site** as **System Manager**

2. **Open Xero Settings**:
   - Use **Awesome Bar** (press `/` or `Ctrl+K`) → type `Xero Settings`
   - OR navigate to **Integrations** → **Xero Settings**

3. **Enter Xero Credentials**:
   - **Client ID**: Paste your Xero Client ID
   - **Client Secret**: Paste your Xero Client Secret
   - **Redirect URI**: 
     ```
     https://your-site.frappe.cloud/api/method/erpnext_xero_app.xero_integration.api.xero_oauth_callback
     ```
   - Click **Save**

4. **Test Connection**:
   - Click the **"Test Connection"** button
   - You should see a success message if credentials are valid
   - ⚠️ **Note**: If you haven't completed OAuth yet, you'll need to manually enter `access_token`, `refresh_token`, and `tenant_id` first (see Step 6)

5. **Try Sync Buttons**:
   - Click **"Sync Customers Now"** or **"Sync Invoices Now"**
   - These will trigger the sync logic (may show errors if mapping storage isn't implemented yet)

---

## Step 6: Complete OAuth Flow (Manual for Now)

**Currently, the app doesn't have a full OAuth redirect handler yet.** To test immediately:

1. **Get Xero tokens manually**:
   - Use a tool like **Postman** or **curl** to complete OAuth:
     ```bash
     # Step 1: Get authorization URL
     https://login.xero.com/identity/connect/authorize?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&scope=accounting.contacts accounting.transactions offline_access
     
     # Step 2: After authorizing, you'll get a code in the redirect URL
     # Step 3: Exchange code for tokens (use Postman or curl)
     ```

2. **Or use Xero's Postman collection**:
   - Import Xero's Postman collection
   - Follow their OAuth 2.0 flow
   - Copy the `access_token`, `refresh_token`, and `tenant_id`

3. **Paste tokens into ERPNext**:
   - Go back to **Xero Settings**
   - Paste:
     - **Access Token**
     - **Refresh Token**
     - **Tenant ID**
   - Save

4. **Test Connection again** - should work now!

---

## Step 7: Verify Everything Works

### Checklist:

- [ ] App installed successfully (`bench list-apps` shows `erpnext_xero_app`)
- [ ] `Xero Settings` DocType visible in ERPNext UI
- [ ] Can enter Client ID / Secret and save
- [ ] "Test Connection" button works (after tokens are set)
- [ ] "Sync Customers Now" button runs without errors
- [ ] "Sync Invoices Now" button runs without errors

---

## Troubleshooting

### "App not found" error:
- Make sure you ran `bench install-app erpnext_xero_app`
- Check app is in `apps/erpnext_xero_app/` directory
- Verify `hooks.py` has correct `app_name`

### "Permission denied" errors:
- Ensure you're logged in as **System Manager**
- Check DocType permissions in `xero_settings.json`

### "Connection failed" in Test Connection:
- Verify Client ID / Secret are correct
- Check Access Token / Tenant ID are set
- Ensure tokens haven't expired (refresh if needed)

### Sync buttons don't work:
- Ensure you completed **Connect to Xero** (tokens + tenant ID saved)
- Ensure required defaults are set in **Xero Settings** (e.g. Xero Sales Account Code)
- Check browser console for JavaScript errors

---

## Next Steps (After Testing)

Once basic testing works:

1. Enable/disable sync directions in **Xero Settings**
2. Review **Xero Sync Log** for any failures
3. Validate mappings in **Xero Mapping**
4. Test with real data (small batch first)

---

## Support

- **Frappe Cloud Docs**: https://frappecloud.com/docs
- **Frappe Framework Docs**: https://frappeframework.com/docs
- **Xero API Docs**: https://developer.xero.com/documentation

---

**Last Updated**: [Current Date]  
**Status**: Ready for Frappe Cloud deployment
