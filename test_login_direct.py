#!/usr/bin/env python3
"""
Direct login test to isolate base64 error
"""

import traceback
from database.connection import SnowflakeConnection
from utils.auth.auth_utils import verify_password
from utils.business.business_auth import create_business_session

def test_full_login_flow():
    """Test the complete login flow"""
    print("=" * 50)
    print("TESTING COMPLETE LOGIN FLOW")
    print("=" * 50)
    
    email = "jtmanningm@gmail.com"
    password = "Cougars$24"
    
    try:
        print(f"1. Testing login for: {email}")
        
        # Get database connection
        conn = SnowflakeConnection.get_instance()
        print("✅ Database connection established")
        
        # Try business login query
        print("2. Querying business portal users...")
        query = """
        SELECT 
            PORTAL_USER_ID,
            PASSWORD_HASH,
            IS_ACTIVE
        FROM OPERATIONAL.BARBER.BUSINESS_PORTAL_USERS
        WHERE EMAIL = ?
        """
        
        result = conn.execute_query(query, [email.lower()])
        print(f"✅ Query executed, results: {len(result) if result else 0}")
        
        if result and len(result) > 0:
            user = result[0]
            print(f"✅ User found: {user['PORTAL_USER_ID']}")
            
            # Test password verification
            print("3. Verifying password...")
            if verify_password(password, user['PASSWORD_HASH']):
                print("✅ Password verified")
                
                # Test session creation
                print("4. Creating business session...")
                session_id = create_business_session(
                    user['PORTAL_USER_ID'],
                    'test-ip',
                    'test-agent'
                )
                
                if session_id:
                    print(f"✅ Session created: {session_id}")
                    print("🎉 COMPLETE LOGIN FLOW SUCCESSFUL!")
                    return True
                else:
                    print("❌ Session creation failed")
            else:
                print("❌ Password verification failed")
        else:
            print("❌ No user found")
            
        return False
        
    except Exception as e:
        print(f"❌ ERROR in login flow: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_full_login_flow()