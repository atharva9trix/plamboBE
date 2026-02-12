import sqlalchemy as db
from sqlalchemy.engine import URL
from sqlalchemy import text
import yaml
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from src.config.config import Config

config = Config()


# #config
# with open('src/config/config.yml', 'r', encoding='utf8') as ymlfile:
#     meta_data = yaml.load(ymlfile, Loader=yaml.FullLoader)


class Engine:
    def __init__(self):
        self.drivername = config.DB_DRIVERNAME
        self.username = config.DB_USERNAME
        self.password = config.DB_PASSWORD
        self.host = config.DB_HOST
        self.port = config.DB_PORT
        self.db_name = config.DB_DBNAME

    def connect_engine(self, drivername=None, username=None, password=None, host=None, port=None, db_name=None):
        try:
            if drivername == None:
                db_url = URL.create(
                    drivername=self.drivername,
                    username=self.username,
                    password=self.password,
                    host=self.host,
                    port=self.port,
                    database=self.db_name
                )
            else:
                db_url = URL.create(
                    drivername=drivername,
                    username=username,
                    password=password,
                    host=host,
                    port=port,
                    database=db_name
                )

            print(db_url)
            db_engine = db.create_engine(db_url)
            print(db_engine)
            db_conn = db_engine.connect()

            return db_conn, 1
        except Exception as e:
            print(e)

            return f"Failed to connect to DB due to {e}", -1

    def disconnect_engine(self, connection):
        connection.close()
        return "Success"


class Read_Write:
    def fetch_data(self, query, connection):
        try:
            connection.rollback()
            df = pd.read_sql(query, connection)
            return df, 1
        except Exception as e:
            print(e)
            return "Failed to read the table.", -1

    def post_data(self, df, table_name, connection):

        if "Id" in df.columns.values.tolist():
            df = df.drop('Id', axis=1)
        else:
            df = df

        try:
            connection.rollback()
            status = df.to_sql(table_name, connection, schema="public", if_exists="append", index=False, chunksize=1000)
            connection.commit()
            return "Success", 1
        except Exception as e:
            print(e)
            return f"Failed to write into the table. \n {e}", -1

    def update_data(self, query, connection):
        try:
            connection.rollback()
            status = connection.execute(text(query))
            connection.commit()
            return "Success", 1
        except Exception as e:
            print(e)
            return f"Failed to write into the table. \n {e}", -1


if __name__ == '__main__':
    db_conn, status = Engine().connect_engine()
    print(status)
    import pandas as pd

    # z = pd.read_sql("SET search_path TO public;",conn)
    z, status = Read_Write().fetch_data('Select * from "Master_Attribute_Type";', db_conn)
    # z = pd.read_sql("SET search_path TO public; Select * from Account;",conn)
    print(z)
    #
    # za = Read_Write().post_data(z,"Client",db_conn)
    # print(za)

    # z.()
    print("Done")