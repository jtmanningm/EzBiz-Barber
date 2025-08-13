"""
Operating hours configuration utility for Ez_Biz_Barber
"""
import streamlit as st
from datetime import time
from typing import Optional, Tuple, Dict, Any
from database.connection import snowflake_conn


def check_operating_hours_configured() -> bool:
    """
    Check if operating hours are configured in the database or session state.
    
    Returns:
        bool: True if operating hours are configured, False otherwise
    """
    # First check session state (for same-session configuration)
    if st.session_state.get('operating_hours_configured', False):
        return True
        
    try:
        # Check if BUSINESS_INFO table has any records with the required columns
        # Since BARBER schema may not have operating hours columns yet, we'll use a fallback approach
        query = """
        SELECT BUSINESS_ID
        FROM OPERATIONAL.BARBER.BUSINESS_INFO
        ORDER BY MODIFIED_DATE DESC
        LIMIT 1
        """
        
        result = snowflake_conn.execute_query(query)
        
        if result:
            # Try to check for operating hours columns (they may not exist yet)
            try:
                hours_query = """
                SELECT OPERATING_HOURS_START, OPERATING_HOURS_END
                FROM OPERATIONAL.BARBER.BUSINESS_INFO
                WHERE BUSINESS_ID = ?
                """
                hours_result = snowflake_conn.execute_query(hours_query, [result[0]['BUSINESS_ID']])
                
                if hours_result and hours_result[0].get('OPERATING_HOURS_START') and hours_result[0].get('OPERATING_HOURS_END'):
                    return True
            except Exception:
                # Columns don't exist yet, return False
                pass
        
        return False
        
    except Exception as e:
        st.error(f"Error checking business info: {str(e)}")
        return False


def display_operating_hours_setup() -> bool:
    """
    Display a form to set up basic operating hours.
    
    Returns:
        bool: True if operating hours were successfully configured
    """
    st.warning("⚠️ **Operating hours not configured** - You need to set business hours to see available time slots for scheduling.")
    
    with st.expander("⏰ **Set Operating Hours**", expanded=True):
        st.info("💡 Set your basic business hours to enable service scheduling. You can adjust these later in Settings.")
        
        with st.form("quick_operating_hours"):
            # Basic business information
            st.subheader("Basic Business Information")
            business_name = st.text_input(
                "Business Name*",
                placeholder="e.g., Ez Biz Barber Shop",
                help="This will appear on customer communications"
            )
            
            business_phone = st.text_input(
                "Business Phone*", 
                placeholder="(555) 123-4567",
                help="Customer contact number"
            )
            
            business_email = st.text_input(
                "Business Email*",
                placeholder="contact@yourbarbershop.com",
                help="Email for customer communications"
            )
            
            # Address information
            st.subheader("Business Address")
            col1, col2 = st.columns(2)
            with col1:
                street_address = st.text_input("Street Address*", placeholder="123 Main Street")
                city = st.text_input("City*", placeholder="Phoenix")
            with col2:
                state = st.text_input("State*", placeholder="AZ", value="AZ")
                zip_code = st.text_input("ZIP Code*", placeholder="85001")
            
            # Operating hours
            st.subheader("Operating Hours")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Weekdays (Mon-Fri)**")
                weekday_start = st.time_input(
                    "Opening Time",
                    value=time(8, 0),
                    help="When do you open on weekdays?"
                )
                weekday_end = st.time_input(
                    "Closing Time", 
                    value=time(17, 0),
                    help="When do you close on weekdays?"
                )
            
            with col2:
                st.write("**Weekends (Sat-Sun)**")
                weekend_start = st.time_input(
                    "Weekend Opening Time",
                    value=time(9, 0),
                    help="When do you open on weekends?"
                )
                weekend_end = st.time_input(
                    "Weekend Closing Time",
                    value=time(15, 0), 
                    help="When do you close on weekends?"
                )
            
            # Submit button
            submitted = st.form_submit_button(
                "💾 Save Business Info & Operating Hours", 
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                # Validate required fields
                if not all([business_name, business_phone, business_email, street_address, city, state, zip_code]):
                    st.error("Please fill in all required fields marked with *")
                    return False
                
                # Validate time logic
                if weekday_start >= weekday_end:
                    st.error("Weekday closing time must be after opening time")
                    return False
                    
                if weekend_start >= weekend_end:
                    st.error("Weekend closing time must be after opening time")
                    return False
                
                # Save to database
                success = save_business_info_with_hours({
                    'business_name': business_name.strip(),
                    'phone_number': business_phone.strip(),
                    'email_address': business_email.strip(),
                    'street_address': street_address.strip(),
                    'city': city.strip(),
                    'state': state.strip(),
                    'zip_code': zip_code.strip(),
                    'weekday_start': weekday_start,
                    'weekday_end': weekday_end,
                    'weekend_start': weekend_start,
                    'weekend_end': weekend_end
                })
                
                if success:
                    st.success("✅ Business information and operating hours saved successfully!")
                    # Set a session state flag to indicate operating hours are now configured
                    st.session_state['operating_hours_configured'] = True
                    st.session_state['business_hours_data'] = {
                        'weekday_start': weekday_start,
                        'weekday_end': weekday_end,
                        'weekend_start': weekend_start,
                        'weekend_end': weekend_end
                    }
                    st.info("✅ You can now proceed with scheduling below!")
                    return True
                else:
                    st.error("❌ Failed to save business information. Please try again.")
                    return False
    
    return False


def save_business_info_with_hours(data: Dict[str, Any]) -> bool:
    """
    Save business information with operating hours to the database.
    Handles case where operating hours columns may not exist yet.
    
    Args:
        data: Dictionary containing business info and operating hours
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # First check if business info already exists
        check_query = """
        SELECT BUSINESS_ID 
        FROM OPERATIONAL.BARBER.BUSINESS_INFO
        ORDER BY MODIFIED_DATE DESC
        LIMIT 1
        """
        
        existing = snowflake_conn.execute_query(check_query)
        
        # Try to save with operating hours columns first, fallback to basic info if columns don't exist
        try:
            if existing:
                # Update existing record with operating hours
                update_query = """
                UPDATE OPERATIONAL.BARBER.BUSINESS_INFO
                SET BUSINESS_NAME = ?,
                    PHONE_NUMBER = ?,
                    EMAIL_ADDRESS = ?,
                    STREET_ADDRESS = ?,
                    CITY = ?,
                    STATE = ?,
                    ZIP_CODE = ?,
                    OPERATING_HOURS_START = ?,
                    OPERATING_HOURS_END = ?,
                    WEEKEND_OPERATING_HOURS_START = ?,
                    WEEKEND_OPERATING_HOURS_END = ?,
                    ACTIVE_STATUS = TRUE,
                    MODIFIED_DATE = CURRENT_TIMESTAMP()
                WHERE BUSINESS_ID = ?
                """
                
                params = [
                    data['business_name'],
                    data['phone_number'], 
                    data['email_address'],
                    data['street_address'],
                    data['city'],
                    data['state'],
                    data['zip_code'],
                    data['weekday_start'].isoformat(),
                    data['weekday_end'].isoformat(),
                    data['weekend_start'].isoformat(),
                    data['weekend_end'].isoformat(),
                    existing[0]['BUSINESS_ID']
                ]
                
            else:
                # Insert new record with operating hours
                update_query = """
                INSERT INTO OPERATIONAL.BARBER.BUSINESS_INFO (
                    BUSINESS_NAME, PHONE_NUMBER, EMAIL_ADDRESS,
                    STREET_ADDRESS, CITY, STATE, ZIP_CODE,
                    OPERATING_HOURS_START, OPERATING_HOURS_END,
                    WEEKEND_OPERATING_HOURS_START, WEEKEND_OPERATING_HOURS_END,
                    ACTIVE_STATUS, CREATED_DATE, MODIFIED_DATE
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP())
                """
                
                params = [
                    data['business_name'],
                    data['phone_number'],
                    data['email_address'], 
                    data['street_address'],
                    data['city'],
                    data['state'],
                    data['zip_code'],
                    data['weekday_start'].isoformat(),
                    data['weekday_end'].isoformat(),
                    data['weekend_start'].isoformat(),
                    data['weekend_end'].isoformat()
                ]
            
            snowflake_conn.execute_query(update_query, params)
            return True
            
        except Exception as hours_error:
            # Operating hours columns don't exist, save basic business info only
            st.warning("⚠️ Operating hours columns don't exist in database. Saving basic business info only.")
            
            if existing:
                # Update existing record without operating hours
                fallback_query = """
                UPDATE OPERATIONAL.BARBER.BUSINESS_INFO
                SET BUSINESS_NAME = ?,
                    PHONE_NUMBER = ?,
                    EMAIL_ADDRESS = ?,
                    STREET_ADDRESS = ?,
                    CITY = ?,
                    STATE = ?,
                    ZIP_CODE = ?,
                    MODIFIED_DATE = CURRENT_TIMESTAMP()
                WHERE BUSINESS_ID = ?
                """
                
                fallback_params = [
                    data['business_name'],
                    data['phone_number'],
                    data['email_address'],
                    data['street_address'],
                    data['city'],
                    data['state'],
                    data['zip_code'],
                    existing[0]['BUSINESS_ID']
                ]
            else:
                # Insert new record without operating hours
                fallback_query = """
                INSERT INTO OPERATIONAL.BARBER.BUSINESS_INFO (
                    BUSINESS_NAME, PHONE_NUMBER, EMAIL_ADDRESS,
                    STREET_ADDRESS, CITY, STATE, ZIP_CODE,
                    CREATED_DATE, MODIFIED_DATE
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP())
                """
                
                fallback_params = [
                    data['business_name'],
                    data['phone_number'],
                    data['email_address'],
                    data['street_address'],
                    data['city'],
                    data['state'],
                    data['zip_code']
                ]
            
            snowflake_conn.execute_query(fallback_query, fallback_params)
            st.info("💡 Business info saved. Operating hours are stored in session for this scheduling session.")
            return True
        
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return False


def get_business_hours_for_date(service_date) -> Tuple[time, time]:
    """
    Get business hours for a specific date from database or session state.
    Fallback to defaults if not configured.
    
    Args:
        service_date: Date to check business hours for
        
    Returns:
        Tuple of (start_time, end_time) for business hours
    """
    # First check session state for operating hours (for same-session configuration)
    if st.session_state.get('business_hours_data'):
        hours_data = st.session_state['business_hours_data']
        is_weekend = service_date.weekday() >= 5
        
        if is_weekend:
            return hours_data['weekend_start'], hours_data['weekend_end']
        else:
            return hours_data['weekday_start'], hours_data['weekday_end']
    
    try:
        # Try to get from database (may fail if columns don't exist)
        business_hours_query = """
        SELECT 
            OPERATING_HOURS_START,
            OPERATING_HOURS_END,
            WEEKEND_OPERATING_HOURS_START,
            WEEKEND_OPERATING_HOURS_END
        FROM OPERATIONAL.BARBER.BUSINESS_INFO
        ORDER BY MODIFIED_DATE DESC
        LIMIT 1
        """
        
        business_hours_result = snowflake_conn.execute_query(business_hours_query)
        
        if business_hours_result:
            business_info = business_hours_result[0]
            # Check if it's weekend (Saturday = 5, Sunday = 6)
            is_weekend = service_date.weekday() >= 5
            
            # Get appropriate hours based on weekday/weekend
            if is_weekend:
                start_time_str = business_info.get('WEEKEND_OPERATING_HOURS_START')
                end_time_str = business_info.get('WEEKEND_OPERATING_HOURS_END')
            else:
                start_time_str = business_info.get('OPERATING_HOURS_START')
                end_time_str = business_info.get('OPERATING_HOURS_END')
            
            # Parse time strings, fallback to defaults if parsing fails
            try:
                business_start = time.fromisoformat(str(start_time_str)) if start_time_str else time(8, 0)
                business_end = time.fromisoformat(str(end_time_str)) if end_time_str else time(17, 0)
                return business_start, business_end
            except (ValueError, TypeError):
                pass
        
        # Fallback to defaults if no business hours found or parsing failed
        return time(8, 0), time(17, 0)
        
    except Exception as e:
        # Database query failed (likely columns don't exist), fallback to defaults
        return time(8, 0), time(17, 0)