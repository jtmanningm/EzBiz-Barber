# Streamlit Cloud Deployment Guide

This guide will help you deploy the Ez_Biz Barber application to Streamlit Cloud.

## Prerequisites

1. **GitHub Repository**: ✅ Already created at `https://github.com/jtmanningm/EzBiz-Barber`
2. **Snowflake Database**: You need access to a Snowflake account with the OPERATIONAL.BARBER schema created
3. **Streamlit Cloud Account**: Sign up at [share.streamlit.io](https://share.streamlit.io)

## Step 1: Create Snowflake Database Schema

1. **Run the Schema Creation Script**:
   ```sql
   -- Execute the entire create_barber_schema.sql file in your Snowflake environment
   -- This creates all necessary tables in the OPERATIONAL.BARBER schema
   ```

2. **Note Your Snowflake Connection Details**:
   - Account identifier (e.g., `abc12345.us-east-1`)
   - Username
   - Password
   - Warehouse name
   - Database name
   - Role name

## Step 2: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**: Visit [share.streamlit.io](https://share.streamlit.io)

2. **Sign in** with your GitHub account

3. **Create New App**:
   - Click "New app"
   - **Repository**: `jtmanningm/EzBiz-Barber`
   - **Branch**: `main`
   - **Main file path**: `main.py`
   - **App URL**: Choose a custom URL (e.g., `your-barber-shop`)

4. **Configure Secrets**:
   - Click "Advanced settings" 
   - Add the following secrets in TOML format:

```toml
[snowflake]
account = "your-snowflake-account-identifier"
user = "your-username"
password = "your-password"
warehouse = "your-warehouse"
database = "your-database"
schema = "BARBER"
role = "your-role"

[email]
smtp_server = "smtp.gmail.com"
smtp_port = 587
email_address = "your-email@gmail.com"
email_password = "your-app-password"

[business]
business_name = "Your Barber Shop"
contact_email = "info@yourbarbershop.com"
contact_phone = "(555) 123-4567"

[app]
debug_mode = false
session_timeout = 3600
```

5. **Deploy**: Click "Deploy!"

## Step 3: Initial Setup

Once deployed, you'll need to:

1. **Add Services**: Go to Settings → Services and add your barber services
2. **Add Employees**: Go to Settings → Employees and add your staff
3. **Create Admin User**: Register a business portal user for administration
4. **Test Functionality**: Create a test customer and booking

## Step 4: Configure Email (Optional)

For email notifications:

1. **Gmail Setup** (recommended):
   - Enable 2-factor authentication
   - Generate an "App Password" 
   - Use the app password in the `email_password` field

2. **Other Email Providers**:
   - Update `smtp_server` and `smtp_port` accordingly
   - Check your provider's SMTP settings

## Troubleshooting

### Common Issues:

1. **Snowflake Connection Error**:
   - Verify your account identifier format
   - Ensure your IP is whitelisted in Snowflake
   - Check username/password/role permissions

2. **Missing Dependencies**:
   - All dependencies are in `requirements.txt`
   - Streamlit Cloud automatically installs them

3. **Database Schema Issues**:
   - Ensure `create_barber_schema.sql` was run completely
   - Verify all tables exist in OPERATIONAL.BARBER

4. **Authentication Issues**:
   - Create your first business user manually in the database
   - Or use the registration page if enabled

## Features Available After Deployment

- **📅 Appointment Scheduling**
- **👥 Customer Management** 
- **💰 Payment Processing**
- **👷 Employee Management**
- **📊 Business Analytics**
- **📧 Email Notifications**
- **🔐 Secure Authentication**

## Security Notes

- Never commit secrets to GitHub
- Use strong passwords for all accounts
- Regularly update your Snowflake credentials
- Monitor access logs in Streamlit Cloud

## Support

If you encounter issues:
1. Check the Streamlit Cloud logs
2. Verify your Snowflake connection
3. Ensure all environment variables are set correctly

## App URLs

After deployment, your app will be available at:
- **Public URL**: `https://your-app-name.streamlit.app`
- **Admin Access**: Use the business portal login
- **Customer Access**: Customers can register and login

Enjoy your new barber shop management system! 💈