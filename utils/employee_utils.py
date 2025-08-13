"""
Employee management utility for Ez_Biz_Barber
"""
import streamlit as st
from typing import Optional, List, Dict, Any
from database.connection import snowflake_conn


def get_all_employees() -> List[Dict[str, Any]]:
    """
    Get all active employees from the database.
    
    Returns:
        List of employee dictionaries
    """
    try:
        query = """
        SELECT 
            EMPLOYEE_ID,
            FIRST_NAME,
            LAST_NAME,
            EMAIL,
            PHONE_NUMBER,
            JOB_TITLE,
            HOURLY_RATE,
            STATUS,
            IS_ACTIVE
        FROM OPERATIONAL.BARBER.EMPLOYEE
        WHERE IS_ACTIVE = TRUE
        ORDER BY LAST_NAME, FIRST_NAME
        """
        
        result = snowflake_conn.execute_query(query)
        return result if result else []
        
    except Exception as e:
        st.error(f"Error fetching employees: {str(e)}")
        return []


def create_employee(employee_data: Dict[str, Any]) -> Optional[int]:
    """
    Create a new employee in the database.
    
    Args:
        employee_data: Dictionary containing employee information
        
    Returns:
        Employee ID if successful, None otherwise
    """
    try:
        insert_query = """
        INSERT INTO OPERATIONAL.BARBER.EMPLOYEE (
            FIRST_NAME,
            LAST_NAME,
            EMAIL,
            PHONE_NUMBER,
            JOB_TITLE,
            HOURLY_RATE,
            STATUS,
            HIRE_DATE,
            IS_ACTIVE
        ) VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE', CURRENT_DATE(), TRUE)
        """
        
        params = [
            employee_data['first_name'],
            employee_data['last_name'],
            employee_data.get('email', ''),
            employee_data.get('phone_number', ''),
            employee_data.get('job_title', 'Barber'),
            employee_data.get('hourly_rate', 0.0)
        ]
        
        snowflake_conn.execute_query(insert_query, params)
        
        # Get the newly created employee ID
        id_query = """
        SELECT EMPLOYEE_ID 
        FROM OPERATIONAL.BARBER.EMPLOYEE 
        WHERE FIRST_NAME = ? AND LAST_NAME = ?
        ORDER BY EMPLOYEE_ID DESC 
        LIMIT 1
        """
        
        result = snowflake_conn.execute_query(id_query, [
            employee_data['first_name'], 
            employee_data['last_name']
        ])
        
        if result:
            employee_id = result[0]['EMPLOYEE_ID']
            st.success(f"✅ Employee '{employee_data['first_name']} {employee_data['last_name']}' created successfully!")
            return employee_id
        else:
            st.error("Failed to retrieve new employee ID")
            return None
            
    except Exception as e:
        st.error(f"Error creating employee: {str(e)}")
        return None


def display_employee_selector_with_creation(key_suffix: str = "", required: bool = False) -> Optional[int]:
    """
    Display employee selector with option to create new employee.
    
    Args:
        key_suffix: Suffix for unique session state keys
        required: Whether employee selection is required
        
    Returns:
        Selected employee ID or None
    """
    # Get existing employees
    employees = get_all_employees()
    
    # Create options list
    employee_options = ["None"]
    employee_map = {}
    
    if employees:
        for emp in employees:
            full_name = f"{emp['FIRST_NAME']} {emp['LAST_NAME']}"
            if emp.get('JOB_TITLE'):
                display_name = f"{full_name} ({emp['JOB_TITLE']})"
            else:
                display_name = full_name
            employee_options.append(display_name)
            employee_map[display_name] = emp['EMPLOYEE_ID']
    
    employee_options.append("+ Create New Employee")
    
    # Initialize session state for employee creation
    create_key = f'show_create_employee_{key_suffix}'
    if create_key not in st.session_state:
        st.session_state[create_key] = False
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_employee = st.selectbox(
            f"Assign Employee {'*' if required else ''}",
            options=employee_options,
            key=f"employee_select_{key_suffix}",
            help="Select an employee to assign to this service"
        )
    
    with col2:
        if selected_employee == "+ Create New Employee":
            st.session_state[create_key] = True
        elif st.session_state[create_key]:
            if st.button("Cancel", key=f"cancel_employee_{key_suffix}", use_container_width=True):
                st.session_state[create_key] = False
                st.rerun()
    
    # Handle employee creation
    if st.session_state[create_key]:
        st.markdown("---")
        with st.expander("👤 **Create New Employee**", expanded=True):
            with st.form(f"create_employee_form_{key_suffix}"):
                st.markdown("#### Add New Employee")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    first_name = st.text_input(
                        "First Name*",
                        key=f"emp_first_name_{key_suffix}"
                    )
                    email = st.text_input(
                        "Email",
                        key=f"emp_email_{key_suffix}",
                        placeholder="employee@barbershop.com"
                    )
                
                with col2:
                    last_name = st.text_input(
                        "Last Name*",
                        key=f"emp_last_name_{key_suffix}"
                    )
                    phone_number = st.text_input(
                        "Phone Number",
                        key=f"emp_phone_{key_suffix}",
                        placeholder="(555) 123-4567"
                    )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    job_title = st.selectbox(
                        "Job Title",
                        options=[
                            "Barber",
                            "Senior Barber", 
                            "Barber Assistant",
                            "Manager",
                            "Owner",
                            "Receptionist",
                            "Other"
                        ],
                        key=f"emp_job_title_{key_suffix}"
                    )
                
                with col2:
                    hourly_rate = st.number_input(
                        "Hourly Rate ($)",
                        min_value=0.0,
                        max_value=200.0,
                        step=0.50,
                        format="%.2f",
                        key=f"emp_hourly_rate_{key_suffix}"
                    )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    create_button = st.form_submit_button(
                        "Create Employee",
                        type="primary",
                        use_container_width=True
                    )
                
                with col2:
                    cancel_button = st.form_submit_button(
                        "Cancel",
                        use_container_width=True
                    )
                
                if cancel_button:
                    st.session_state[create_key] = False
                    st.rerun()
                
                if create_button:
                    # Validate required fields
                    if not first_name or not last_name:
                        st.error("First name and last name are required")
                    elif len(first_name.strip()) == 0 or len(last_name.strip()) == 0:
                        st.error("First name and last name cannot be empty")
                    else:
                        # Create the employee
                        employee_data = {
                            'first_name': first_name.strip(),
                            'last_name': last_name.strip(),
                            'email': email.strip() if email else '',
                            'phone_number': phone_number.strip() if phone_number else '',
                            'job_title': job_title,
                            'hourly_rate': hourly_rate
                        }
                        
                        new_employee_id = create_employee(employee_data)
                        
                        if new_employee_id:
                            # Reset the form and return to selection
                            st.session_state[create_key] = False
                            st.info("🔄 Employee created! Please reselect from the dropdown above.")
                            st.rerun()
        
        # Don't continue while creating employee
        return None
    
    # Return selected employee ID
    if selected_employee == "None":
        return None
    elif selected_employee == "+ Create New Employee":
        return None
    elif selected_employee in employee_map:
        return employee_map[selected_employee]
    else:
        return None


def get_employee_display_name(employee_id: int) -> str:
    """
    Get display name for an employee.
    
    Args:
        employee_id: Employee ID
        
    Returns:
        Display name string
    """
    if not employee_id:
        return "No Employee Assigned"
    
    try:
        query = """
        SELECT FIRST_NAME, LAST_NAME, JOB_TITLE
        FROM OPERATIONAL.BARBER.EMPLOYEE
        WHERE EMPLOYEE_ID = ?
        """
        
        result = snowflake_conn.execute_query(query, [employee_id])
        
        if result:
            emp = result[0]
            name = f"{emp['FIRST_NAME']} {emp['LAST_NAME']}"
            if emp.get('JOB_TITLE'):
                return f"{name} ({emp['JOB_TITLE']})"
            return name
        else:
            return f"Employee #{employee_id} (Not Found)"
            
    except Exception as e:
        return f"Employee #{employee_id} (Error: {str(e)})"