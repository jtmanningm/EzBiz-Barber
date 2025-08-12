#!/usr/bin/env python3
"""
Generate comprehensive schema comparison between OPERATIONAL.CARPET and OPERATIONAL.BARBER
"""

from database.connection import SnowflakeConnection

def compare_schemas():
    """Compare all aspects of CARPET vs BARBER schemas"""
    conn = SnowflakeConnection.get_instance()
    
    print("=" * 60)
    print("SCHEMA COMPARISON: OPERATIONAL.CARPET vs OPERATIONAL.BARBER")
    print("=" * 60)
    
    # Get all tables in both schemas
    carpet_tables_query = """
    SELECT TABLE_NAME, TABLE_TYPE 
    FROM OPERATIONAL.INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_SCHEMA = 'CARPET' AND TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_NAME
    """
    
    barber_tables_query = """
    SELECT TABLE_NAME, TABLE_TYPE 
    FROM OPERATIONAL.INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_SCHEMA = 'BARBER' AND TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_NAME
    """
    
    try:
        carpet_tables = conn.execute_query(carpet_tables_query)
        barber_tables = conn.execute_query(barber_tables_query)
        
        carpet_table_names = {t['TABLE_NAME'] for t in carpet_tables}
        barber_table_names = {t['TABLE_NAME'] for t in barber_tables}
        
        print(f"\n📊 TABLE COUNT COMPARISON:")
        print(f"CARPET: {len(carpet_table_names)} tables")
        print(f"BARBER: {len(barber_table_names)} tables")
        
        # Find table differences
        only_in_carpet = carpet_table_names - barber_table_names
        only_in_barber = barber_table_names - carpet_table_names
        common_tables = carpet_table_names & barber_table_names
        
        if only_in_carpet:
            print(f"\n❌ TABLES ONLY IN CARPET: {sorted(only_in_carpet)}")
        
        if only_in_barber:
            print(f"\n❌ TABLES ONLY IN BARBER: {sorted(only_in_barber)}")
        
        if not only_in_carpet and not only_in_barber:
            print(f"\n✅ All tables exist in both schemas")
        
        print(f"\n📋 COMMON TABLES ({len(common_tables)}):")
        for table in sorted(common_tables):
            print(f"  - {table}")
        
        # Compare columns for each common table
        print(f"\n" + "=" * 40)
        print("COLUMN COMPARISON FOR EACH TABLE")
        print("=" * 40)
        
        for table_name in sorted(common_tables):
            print(f"\n🔍 Comparing table: {table_name}")
            compare_table_columns(conn, table_name)
            
    except Exception as e:
        print(f"❌ Error comparing schemas: {e}")

def compare_table_columns(conn, table_name):
    """Compare columns between CARPET and BARBER for a specific table"""
    
    carpet_cols_query = f"""
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, ORDINAL_POSITION
    FROM OPERATIONAL.INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'CARPET' AND TABLE_NAME = '{table_name}'
    ORDER BY ORDINAL_POSITION
    """
    
    barber_cols_query = f"""
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, ORDINAL_POSITION
    FROM OPERATIONAL.INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'BARBER' AND TABLE_NAME = '{table_name}'
    ORDER BY ORDINAL_POSITION
    """
    
    try:
        carpet_cols = conn.execute_query(carpet_cols_query)
        barber_cols = conn.execute_query(barber_cols_query)
        
        # Create sets of column info for comparison
        carpet_col_info = {
            (col['COLUMN_NAME'], col['DATA_TYPE'], col['IS_NULLABLE']) 
            for col in carpet_cols
        }
        barber_col_info = {
            (col['COLUMN_NAME'], col['DATA_TYPE'], col['IS_NULLABLE']) 
            for col in barber_cols
        }
        
        carpet_col_names = {col[0] for col in carpet_col_info}
        barber_col_names = {col[0] for col in barber_col_info}
        
        # Find differences
        only_in_carpet_cols = carpet_col_names - barber_col_names
        only_in_barber_cols = barber_col_names - carpet_col_names
        
        if only_in_carpet_cols:
            print(f"  ❌ Columns only in CARPET: {sorted(only_in_carpet_cols)}")
            
        if only_in_barber_cols:
            print(f"  ❌ Columns only in BARBER: {sorted(only_in_barber_cols)}")
        
        # Check for type mismatches in common columns
        common_cols = carpet_col_names & barber_col_names
        type_mismatches = []
        
        for col_name in common_cols:
            carpet_col = next(col for col in carpet_col_info if col[0] == col_name)
            barber_col = next(col for col in barber_col_info if col[0] == col_name)
            
            if carpet_col[1:] != barber_col[1:]:  # Compare type and nullable
                type_mismatches.append({
                    'column': col_name,
                    'carpet': f"{carpet_col[1]} ({'NULL' if carpet_col[2] == 'YES' else 'NOT NULL'})",
                    'barber': f"{barber_col[1]} ({'NULL' if barber_col[2] == 'YES' else 'NOT NULL'})"
                })
        
        if type_mismatches:
            print(f"  ⚠️ Type mismatches:")
            for mismatch in type_mismatches:
                print(f"    {mismatch['column']}: CARPET={mismatch['carpet']}, BARBER={mismatch['barber']}")
        
        if not only_in_carpet_cols and not only_in_barber_cols and not type_mismatches:
            print(f"  ✅ {table_name}: Columns match perfectly")
        
        print(f"  📊 Column count - CARPET: {len(carpet_col_names)}, BARBER: {len(barber_col_names)}")
        
    except Exception as e:
        print(f"  ❌ Error comparing {table_name}: {e}")

if __name__ == "__main__":
    compare_schemas()