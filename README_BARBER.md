# Ez_Biz Barber Instance

This is a complete copy of the Ez_Biz application configured for the **OPERATIONAL.BARBER** schema instead of OPERATIONAL.CARPET.

## What's Different

- **Schema References**: All database queries now reference `OPERATIONAL.BARBER.*` tables
- **Identical Functionality**: All features, pages, and functionality remain exactly the same
- **Separate Database**: Uses completely separate tables, allowing independent data and customization

## Setup Instructions

### 1. Create the Database Schema
Run the provided SQL script to create all necessary tables:
```sql
-- Execute the entire create_barber_schema.sql file in your Snowflake environment
```

### 2. Run the Application
```bash
cd Ez_Biz_Barber
streamlit run main.py --server.port 8505
```
*Note: Using port 8505 to avoid conflicts with the carpet instance*

### 3. Initial Configuration

1. **Business Information**: Update the business info in the database:
   ```sql
   UPDATE OPERATIONAL.BARBER.BUSINESS_INFO 
   SET BUSINESS_NAME = 'Your Barber Shop Name',
       CONTACT_EMAIL = 'your@email.com',
       CONTACT_PHONE = 'your-phone-number'
   WHERE BUSINESS_ID = 1;
   ```

2. **Add Services**: Create your barber services:
   ```sql
   INSERT INTO OPERATIONAL.BARBER.SERVICES (SERVICE_NAME, SERVICE_CATEGORY, COST, SERVICE_DURATION)
   VALUES 
   ('Haircut', 'Basic Services', 25.00, 30),
   ('Beard Trim', 'Basic Services', 15.00, 15),
   ('Shampoo & Style', 'Premium Services', 35.00, 45),
   ('Hot Towel Shave', 'Premium Services', 40.00, 45);
   ```

3. **Add Employees**: Add your barber staff:
   ```sql
   INSERT INTO OPERATIONAL.BARBER.EMPLOYEE (FIRST_NAME, LAST_NAME, EMAIL, JOB_TITLE, HOURLY_RATE)
   VALUES 
   ('John', 'Smith', 'john@yourbarbershop.com', 'Head Barber', 25.00),
   ('Mike', 'Johnson', 'mike@yourbarbershop.com', 'Barber', 20.00);
   ```

4. **Create Business Portal User**: Create admin access:
   ```sql
   INSERT INTO OPERATIONAL.BARBER.BUSINESS_PORTAL_USERS (EMPLOYEE_ID, EMAIL, PASSWORD_HASH)
   VALUES (1, 'admin@yourbarbershop.com', 'your-hashed-password');
   ```

## Features Available

All the same features as the carpet cleaning version:

- **📅 Scheduling System**: Book and manage appointments
- **👥 Customer Management**: Customer portal and profiles  
- **💰 Transaction Management**: Service breakdown, discounts, payments
- **👷 Employee Management**: Staff assignments and tracking
- **📊 Reporting**: Completed services, revenue tracking
- **📧 Communications**: Email notifications and templates
- **🔐 Authentication**: Separate business and customer portals

## File Structure

```
Ez_Biz_Barber/
├── main.py                          # Main application entry point
├── create_barber_schema.sql          # Database schema creation script
├── database_fixes.sql                # Updated for BARBER schema
├── pages/                           # All application pages
├── models/                          # Data models (updated for BARBER)
├── utils/                           # Utility functions
├── database/                        # Database connection utilities
└── README_BARBER.md                 # This file
```

## Running Both Instances

You can run both the carpet and barber instances simultaneously:

- **Carpet Instance**: `http://localhost:8501` (default port)
- **Barber Instance**: `http://localhost:8505` (specified port)

Each instance will have completely separate data and can be customized independently.

## Database Tables Created

The schema includes all necessary tables:
- Business Information & Services
- Customer Management & Portal Users  
- Service Transactions & Scheduling
- Employee Management & Assignments
- Authentication & Session Management
- Communication & Marketing Tools
- Logging & Security Features

## Next Steps

1. Run the database schema creation script
2. Configure your business-specific information
3. Add your services and employees
4. Test the application functionality
5. Customize as needed for your barber shop operations