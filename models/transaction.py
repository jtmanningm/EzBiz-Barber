from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import streamlit as st
import pandas as pd
from database.connection import SnowflakeConnection
from models.service import fetch_services
import json

@dataclass
class TransactionModel:
    transaction_id: Optional[int] = None
    service_id: int = 0
    customer_id: int = 0
    amount: float = 0.0
    payment_type: str = "Cash"
    transaction_date: datetime = None
    status: str = "Pending"
    notes: Optional[str] = None
    is_deposit: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_id": self.service_id,
            "customer_id": self.customer_id,
            "amount": self.amount,
            "payment_type": self.payment_type,
            "transaction_date": self.transaction_date or datetime.now(),
            "status": self.status,
            "notes": self.notes,
            "is_deposit": self.is_deposit
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransactionModel':
        return cls(
            transaction_id=data.get('TRANSACTION_ID'),
            service_id=data.get('SERVICE_ID', 0),
            customer_id=data.get('CUSTOMER_ID', 0),
            amount=data.get('AMOUNT', 0.0),
            payment_type=data.get('PAYMENT_TYPE', 'Cash'),
            transaction_date=data.get('SERVICE_DATE', datetime.now()),
            status=data.get('STATUS', 'Pending'),
            notes=data.get('NOTES'),
            is_deposit=data.get('IS_DEPOSIT', False)
        )

# Get database connection
snowflake_conn = SnowflakeConnection.get_instance()

def get_service_costs(service_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """Get costs and details for specified services"""
    if not service_ids:
        return {}
        
    ids_str = ', '.join(str(id) for id in service_ids)
    query = f"""
    SELECT SERVICE_ID, SERVICE_NAME, COST
    FROM OPERATIONAL.BARBER.SERVICES
    WHERE SERVICE_ID IN ({ids_str})
    """
    
    try:
        results = snowflake_conn.execute_query(query)
        return {
            row['SERVICE_ID']: {
                'name': row['SERVICE_NAME'],
                'cost': float(row.get('COST', 0.0))  # Added .get() with default value
            } for row in results
        }
    except Exception as e:
        st.error(f"Error fetching service costs: {str(e)}")
        return {}

def get_additional_services(transaction_id):
    """
    Fetch primary and additional services with their costs.
    Returns full service details for properly calculating total cost.
    """
    query = """
    SELECT 
        st.ID as TRANSACTION_ID,
        st.SERVICE_ID as PRIMARY_SERVICE_ID,
        s1.SERVICE_NAME as PRIMARY_SERVICE_NAME,
        s1.COST as PRIMARY_COST,
        st.SERVICE2_ID,
        s2.SERVICE_NAME as SERVICE2_NAME,
        s2.COST as SERVICE2_COST,
        st.SERVICE3_ID,
        s3.SERVICE_NAME as SERVICE3_NAME,
        s3.COST as SERVICE3_COST
    FROM OPERATIONAL.BARBER.SERVICE_TRANSACTION st
    LEFT JOIN OPERATIONAL.BARBER.SERVICES s1 ON st.SERVICE_ID = s1.SERVICE_ID
    LEFT JOIN OPERATIONAL.BARBER.SERVICES s2 ON st.SERVICE2_ID = s2.SERVICE_ID
    LEFT JOIN OPERATIONAL.BARBER.SERVICES s3 ON st.SERVICE3_ID = s3.SERVICE_ID
    WHERE st.ID = :1
    """
    result = snowflake_conn.execute_query(query, [transaction_id])
    
    if not result or not result[0]:
        return None, None, 0.0
    
    service2_id = result[0].get('SERVICE2_ID')
    service3_id = result[0].get('SERVICE3_ID')
    total_cost = float(result[0].get('PRIMARY_COST') or 0.0)
    
    if service2_id:
        total_cost += float(result[0].get('SERVICE2_COST') or 0.0)
    if service3_id:
        total_cost += float(result[0].get('SERVICE3_COST') or 0.0)
    
    return service2_id, service3_id, total_cost


def save_transaction(transaction_data: Dict[str, Any]) -> bool:
    """Save completed transaction with pricing details"""
    try:
        print("Saving transaction with data:", transaction_data)
        service_id = int(transaction_data['service_id'])
        
        # First, validate that the service exists
        validate_query = """
        SELECT COUNT(*) as RECORD_COUNT
        FROM OPERATIONAL.BARBER.SERVICE_TRANSACTION
        WHERE ID = ?
        """
        validation = snowflake_conn.execute_query(validate_query, [service_id])
        print(f"Validation result: {validation}")
        
        if not validation or validation[0]['RECORD_COUNT'] == 0:
            print(f"Service ID {service_id} not found")
            return False

        # Debug: Print current record
        current_record_query = """
        SELECT ID, STATUS, COMPLETION_DATE
        FROM OPERATIONAL.BARBER.SERVICE_TRANSACTION
        WHERE ID = ?
        """
        current_record = snowflake_conn.execute_query(current_record_query, [service_id])
        print(f"Current record before update: {current_record}")

        # Convert price details to JSON
        price_details = transaction_data.get('price_details', {})
        price_adjustments_json = json.dumps({
            'base_cost': float(price_details.get('base_cost', 0)),
            'labor_cost': float(price_details.get('labor_cost', 0)),
            'material_cost': float(price_details.get('material_cost', 0)),
            'adjustment_amount': float(price_details.get('adjustment_amount', 0)),
            'final_price': float(price_details.get('final_price', 0))
        })

        # Build update query
        query = """
        UPDATE OPERATIONAL.BARBER.SERVICE_TRANSACTION
        SET 
            STATUS = 'COMPLETED',
            COMPLETION_DATE = CURRENT_DATE(),
            AMOUNT = ?,
            DISCOUNT = ?,
            AMOUNT_RECEIVED = ?,
            PYMT_MTHD_1 = ?,
            PYMT_MTHD_1_AMT = ?,
            PYMT_MTHD_2 = ?,
            PYMT_MTHD_2_AMT = ?,
            EMPLOYEE1_ID = ?,
            EMPLOYEE2_ID = ?,
            EMPLOYEE3_ID = ?,
            START_TIME = ?,
            END_TIME = ?,
            COMMENTS = ?,
            BASE_SERVICE_COST = ?,
            TOTAL_LABOR_COST = ?,
            MATERIAL_COST = ?,
            PRICE_ADJUSTMENTS_JSON = ?,
            LAST_MODIFIED_DATE = CURRENT_TIMESTAMP()
        WHERE ID = ?
        """
        
        # Convert np.int64 to regular int and ensure default
        employee1_id = int(transaction_data.get('employee1_id', 0)) if transaction_data.get('employee1_id') is not None else None
        employee2_id = int(transaction_data.get('employee2_id', 0)) if transaction_data.get('employee2_id') is not None else None
        employee3_id = int(transaction_data.get('employee3_id', 0)) if transaction_data.get('employee3_id') is not None else None
        
        params = [
            float(transaction_data['final_amount']),
            float(transaction_data.get('discount', 0)),
            float(transaction_data['amount_received']),
            transaction_data.get('payment_method_1'),
            float(transaction_data.get('payment_amount_1', 0)),
            transaction_data.get('payment_method_2'),
             float(transaction_data.get('payment_amount_2',0)),
            employee1_id,
            employee2_id,
            employee3_id,
            str(transaction_data['start_time']),
            str(transaction_data['end_time']),
            str(transaction_data['notes']),
            float(price_details.get('base_cost', 0)),
            float(price_details.get('labor_cost', 0)),
            float(price_details.get('material_cost', 0)),
            price_adjustments_json,
            service_id
        ]

        print(f"Executing transaction update for ID: {service_id}")
        snowflake_conn.execute_query(query, params)

        # Verify the update
        verification = verify_save(service_id)
        if not verification:
            print(f"Failed to verify update for ID: {service_id}")
            return False

        print(f"Successfully updated service  {service_id} to completed status")
        return True

    except Exception as e:
        print(f"Error saving transaction: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

def verify_save(service_id: int) -> Dict[str, Any]:
    """Verify transaction was saved correctly"""
    try:
        query = """
        SELECT ID, STATUS, COMPLETION_DATE, AMOUNT, AMOUNT_RECEIVED
        FROM OPERATIONAL.BARBER.SERVICE_TRANSACTION
        WHERE ID = ?
        """
        result = snowflake_conn.execute_query(query, [service_id])
        if result and len(result) > 0:
            # Convert Row object to dictionary using attribute access
            row = result[0]
            status_info = {
                'ID': row.ID,
                'STATUS': row.STATUS,
                'COMPLETION_DATE': row.COMPLETION_DATE,
                'AMOUNT': row.AMOUNT,
                'AMOUNT_RECEIVED': row.AMOUNT_RECEIVED
            }
            print(f"Verification result for service : {service_id}")
            print(f"Status: {status_info.get('STATUS')}")
            print(f"Completion Date: {status_info.get('COMPLETION_DATE')}")
            print(f"Amount: {status_info.get('AMOUNT')}")
            print(f"Amount Received: {status_info.get('AMOUNT_RECEIVED')}")
            return status_info
        return {}
    except Exception as e:
        print(f"Error verifying save: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {}

def verify_transaction_status(service_id: int) -> Dict[str, Any]:
    """Debug helper to verify transaction and service status"""
    try:
        query = f"""
        SELECT 
            ST.STATUS as TRANSACTION_STATUS,
            ST.COMPLETION_DATE,
            US.STATUS as SERVICE_STATUS
        FROM OPERATIONAL.BARBER.SERVICE_TRANSACTION ST
        JOIN OPERATIONAL.BARBER.UPCOMING_SERVICES US ON ST.SERVICE_ID = US.SERVICE_ID
        WHERE ST.SERVICE_ID = {service_id}
        """
        
        result = snowflake_conn.execute_query(query)
        if result and len(result) > 0:
            status_info = dict(result[0])
            print(f"Status check for service : {service_id}")
            for key, value in status_info.items():
                print(f"{key}: {value}")
            return status_info
            
        print(f"No transaction found for service ID {service_id}")
        return {}
            
    except Exception as e:
        print(f"Error verifying transaction status: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {}

def fetch_transaction(transaction_id: int) -> Optional[TransactionModel]:
    """Fetch transaction details by ID"""
    query = f"""
    SELECT *
    FROM OPERATIONAL.BARBER.SERVICE_TRANSACTION
    WHERE ID = {transaction_id}
    """
    result = snowflake_conn.execute_query(query)
    return TransactionModel.from_dict(result[0]) if result else None

def fetch_service_transactions(service_id: int) -> pd.DataFrame:
    """Fetch all transactions for a service"""
    query = f"""
    SELECT 
        t.ID as TRANSACTION_ID, t.AMOUNT, t.PYMT_MTHD_1 as PAYMENT_TYPE,
        t.SERVICE_DATE as TRANSACTION_DATE, t.STATUS, t.COMMENTS as NOTES,
        t.DEPOSIT as IS_DEPOSIT,
        c.FIRST_NAME, c.LAST_NAME
    FROM OPERATIONAL.BARBER.SERVICE_TRANSACTION t
    JOIN OPERATIONAL.BARBER.CUSTOMER c 
        ON t.CUSTOMER_ID = c.CUSTOMER_ID
    WHERE t.SERVICE_ID = {service_id}
    ORDER BY t.SERVICE_DATE DESC
    """
    result = snowflake_conn.execute_query(query)
    if result:
        df = pd.DataFrame(result)
        df['FULL_NAME'] = df['FIRST_NAME'] + " " + df['LAST_NAME']
        return df
    return pd.DataFrame()

def get_customer_balance(customer_id: int) -> float:
    """Get total balance for a customer"""
    query = f"""
    SELECT 
        COALESCE(SUM(t.AMOUNT), 0) as TOTAL_AMOUNT
    FROM OPERATIONAL.BARBER.SERVICE_TRANSACTION t
    WHERE t.CUSTOMER_ID = {customer_id}
    AND t.STATUS = 'COMPLETED'
    """
    result = snowflake_conn.execute_query(query)
    return float(result[0]['TOTAL_AMOUNT']) if result else 0.0

def update_transaction_status(transaction_id: int, status: str) -> bool:
    """Update transaction status"""
    try:
        query = f"""
        UPDATE OPERATIONAL.BARBER.SERVICE_TRANSACTION
        SET 
            STATUS = '{status}',
            LAST_MODIFIED_DATE = CURRENT_TIMESTAMP()
        WHERE ID = {transaction_id}
        """
        snowflake_conn.execute_query(query)
        return True
    except Exception as e:
        st.error(f"Error updating transaction status: {str(e)}")
        return False

def get_transaction_summary(start_date: datetime, end_date: datetime) -> Dict[str, float]:
    """Get transaction summary for a date range"""
    query = f"""
    SELECT 
        COUNT(*) as TOTAL_TRANSACTIONS,
        COALESCE(SUM(AMOUNT), 0) as TOTAL_AMOUNT,
        COALESCE(SUM(CASE WHEN STATUS = 'COMPLETED' THEN AMOUNT ELSE 0 END), 0) as COMPLETED_AMOUNT
    FROM OPERATIONAL.BARBER.SERVICE_TRANSACTION
    WHERE SERVICE_DATE BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
    """
    result = snowflake_conn.execute_query(query)
    if result:
        return {
            "total_transactions": result[0]['TOTAL_TRANSACTIONS'],
            "total_amount": float(result[0]['TOTAL_AMOUNT']),
            "completed_amount": float(result[0]['COMPLETED_AMOUNT'])
        }
    return {
        "total_transactions": 0,
        "total_amount": 0.0,
        "completed_amount": 0.0
    }

if __name__ == "__main__":
    # Can add any debugging or testing code here if needed
    pass