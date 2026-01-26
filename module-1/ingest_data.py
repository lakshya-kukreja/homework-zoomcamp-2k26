import os
import pandas as pd
from sqlalchemy import create_engine
import click

@click.command()
@click.option('--user', required=True, help="PostgreSQL user")
@click.option('--password', required=True, help="PostgreSQL password")
@click.option('--host', required=True, help="PostgreSQL host")
@click.option('--port', required=True, help="PostgreSQL port")
@click.option('--db', required=True, help="PostgreSQL database name")
@click.option('--table', required=True, help="Target Table Name")
@click.option('--url', required=True, help="URL of the data file")
def ingest_data(user, password, host, port, db, table, url):
    
    # 1. Determine the local filename and download
    if url.endswith('.parquet'):
        file_name = 'output.parquet'
    else:
        file_name = 'output.csv'
        
    print(f"Downloading {url}...")
    os.system(f"wget {url} -O {file_name}")

    # 2. Database Connection
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')

    # 3. Read Data based on extension
    print(f"Reading {file_name}...")
    if file_name.endswith('.parquet'):
        df = pd.read_parquet(file_name)
    else:
        # CSVs can be large, but the Zone file is tiny. 
        # Using low_memory=False to avoid DtypeWarnings
        df = pd.read_csv(file_name, low_memory=False)

    # 4. Handle Format-Specific Transformations
    # Only convert dates if they actually exist in the dataframe
    if 'lpep_pickup_datetime' in df.columns:
        print("Converting green taxi timestamps...")
        df.lpep_pickup_datetime = pd.to_datetime(df.lpep_pickup_datetime)
        df.lpep_dropoff_datetime = pd.to_datetime(df.lpep_dropoff_datetime)

    # 5. Ingest to Postgres
    print(f"Inserting data into table '{table}'...")
    # head(0) creates the schema, then we append the data
    df.head(0).to_sql(name=table, con=engine, if_exists='replace', index=False)
    df.to_sql(name=table, con=engine, if_exists='append', index=False)

    print("Ingestion Finished successfully.")

if __name__ == '__main__':
    ingest_data()