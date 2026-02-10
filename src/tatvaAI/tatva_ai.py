import duckdb,os
import json
import pandas as pd
import pyarrow.parquet as pq
from datetime import datetime
from pathlib import Path
# from src.tatva_util.tatvaAi_utils import Tatva_Utils
from src.db_connection.db_engine import Engine,Read_Write
from src.config.config import Config
config = Config()



SESSION_FILE = Path("sessions.json")
if not SESSION_FILE.exists():
    SESSION_FILE.write_text(json.dumps({}))
class TatvaAIMain():

    def __init__(self):
        # self.base_dir = config.OUTPUT_DATA_PATH
        self.conn = duckdb.connect(database=":memory:")
        # self.analysis = DataAnalysis()
        # self.build_query = Tatva_Utils()
        self.db_funct = Read_Write()
        self.connection = Engine()



    def get_user_session_id(self, user_id):
        created_on = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        conn, msg = self.connection.connect_engine()
        print(conn, msg )
        query_ = f"""select "User_Session_Id" from "User_Session" where "User_Id"='{user_id}' and "Flag"=0;"""
        sesion_id_df, msg = self.db_funct.fetch_data(query_, conn)
        session_id = sesion_id_df['User_Session_Id'].to_list()
        print(session_id)

        if len(sesion_id_df) > 0:
            session_id = max(session_id)
            print(session_id)
            status = 1
        else:
            query = '''SELECT COALESCE(MAX("Session_Id"), 0) + 1 as "Session_Id" FROM "User_Session";'''
            df, msg = self.db_funct.fetch_data(query, conn)
            session_id = df['Session_Id'][0]

            data = {"User_Id": user_id, "Session_Id": session_id, "Created_On": created_on, "Status": 'active'}
            data_df = pd.DataFrame([data])
            msg, status = self.db_funct.post_data(data_df, "User_Session", conn)

        if status == 1:
            query = f'''select "User_Session_Id" from "User_Session" where "User_Id"='{user_id}' and "Session_Id"={session_id};'''
            id_df, stats = self.db_funct.fetch_data(query, conn)
            user_session_id = str(id_df['User_Session_Id'][0])
            disc = self.connection.disconnect_engine(conn)
            # sessions = read_sessions()
            # if user_session_id not in sessions:
            #     sessions[user_session_id] = {}
            # write_sessions(sessions)
            return json.dumps({"user_id": user_id, "session_id": user_session_id}, default=str)
        else:
            return {'msg': 'failed to post data in user_session'}
