# db_connector.py
import oracledb
import pandas as pd
from sqlalchemy import create_engine
import sys
import sqlalchemy.dialects.oracle  # Explicitly import to ensure dialect registration

def get_pos_data():
    # Oracle connection details
    config = {
        "user": "BappyTawhid_56691",
        "password": "Typpa$dihwQOH56",
        "host": "192.168.118.165",
        "port": "1521",
        "service_name": "orcldb"
    }
    
    # SQL query for POS data
    query = """
    SELECT DISTINCT  
    isl.ITEM_DESCRIPTION,  
    isl.ITEM_CODE,  
    isl.QUANTITY AS QUANTITY,  
    isl.OPENING_QUANTITY,  
    isl.CLOSING_QUANTITY,  
    CAST(isl.AMOUNT AS NUMBER(19,0)) AS PRICE,  
    isl.INVOICE_NO AS INVOICE_NO,  
    isl.TRANSACTION_DATE AS TRANSACTION_DATE,  
    m.QUANTITY AS AVAILABLE_QUANTITY,  
    ies.NAME AS STORE_NAME
FROM  
    PAIPAI_POS.INV_STOCK_ITEMLEDGER isl  
LEFT JOIN  
    PAIPAI_POS.INV_STORE ies ON isl.STORE_ID = ies.ID  
LEFT JOIN  
    PAIPAI_POS.INV_STOCK_MASTER m ON isl.ITEM_CODE = m.ITEM_CODE  
WHERE  
    isl.ORGANIZATION_ID = 321
    """
    
    # Try direct oracledb connection first
    try:
        # Initialize oracledb connection
        connection = oracledb.connect(
            user=config['user'],
            password=config['password'],
            dsn=f"{config['host']}:{config['port']}/{config['service_name']}"
        )
        
        # Fetch data using oracledb cursor
        cursor = connection.cursor()
        cursor.execute(query)
        
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        
        # Fetch all rows and create DataFrame
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=columns)
        
        cursor.close()
        connection.close()
        
        print("Successfully fetched data using direct oracledb connection.")
        return df
    
    except Exception as e:
        print(f"Direct oracledb connection failed: {str(e)}", file=sys.stderr)
        
        # Fallback to SQLAlchemy connection
        try:
            # Create connection string for SQLAlchemy
            dsn = f"oracle+oracledb://{config['user']}:{config['password']}@{config['host']}:{config['port']}/?service_name={config['service_name']}"
            
            # Create SQLAlchemy engine
            engine = create_engine(dsn)
            
            # Fetch data into pandas DataFrame
            with engine.connect() as connection:
                df = pd.read_sql(query, con=connection)
            print("Successfully fetched data using SQLAlchemy.")
            return df
        
        except Exception as sqlalchemy_e:
            print(f"SQLAlchemy connection failed: {str(sqlalchemy_e)}", file=sys.stderr)
            return None