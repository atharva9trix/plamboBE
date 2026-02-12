import duckdb,os
import json
import pandas as pd
import pyarrow.parquet as pq
from datetime import datetime
from pathlib import Path
from src.tatva_util.tatvaAi_utils import Tatva_Utils
from src.db_connection.db_engine import Engine,Read_Write
from src.config.config import Config
config = Config()



SESSION_FILE = Path("sessions.json")
if not SESSION_FILE.exists():
    SESSION_FILE.write_text(json.dumps({}))
class TatvaAIMain():

    def __init__(self):
        self.base_dir = config.STD_PARQUET_PATH
        self.conn = duckdb.connect(database=":memory:")
        # self.analysis = DataAnalysis()
        # self.build_query = Tatva_Utils()
        self.db_funct = Read_Write()
        self.connection = Engine()
        self.build_query = Tatva_Utils()

    def get_parquet_path(self, base_dir, userid , sessionid ,fl):
        # parquet_path = os.path.join(base_dir, f"{client_id}_sales.paraquet")
        parquet_path = os.path.join(base_dir, f"{userid}_{sessionid}_{fl}.parquet")
        if not os.path.exists(parquet_path):
            raise FileNotFoundError(f"File not found: {parquet_path}")
        return parquet_path

    def get_recent_history(self, session_id, user_id, n=5):
        connect, status = self.connection.connect_engine()
        query = f'''select "Session_Data" from "Session_Management"
                where "User_Id"='{user_id}' and "Session_Id"={session_id};'''
        df_, status = self.db_funct.fetch_data(query, connect)
        if len(df_) > 0:
            dict_data = df_['Session_Data'][0]
        else:
            dict_data = {}
        keys = sorted(dict_data.keys())[-n:]
        result_dict = {k: (dict_data[k]["question"], dict_data[k]["answer"]) for k in keys}
        # sessions = read_sessions()
        # if str(session_id) not in sessions:
        #     return []
        # conv = sessions[str(session_id)]
        # keys = sorted(dict.keys())[-n:]
        # result_dict = {k: (dict[k]["question"], dict[k]["answer"]) for k in keys}
        disconnect = self.connection.disconnect_engine(connect)
        return result_dict



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

    def query_analysis(self, userid, session_id, question, fl):
        parquet_path = self.get_parquet_path(self.base_dir, userid, session_id,fl)

        if not os.path.exists(parquet_path):
            return {"error": "File not found"}

        try:
            parquet_file = pq.ParquetFile(parquet_path)
            print(parquet_file)
            columns = parquet_file.schema.names
        except Exception as e:
            return {"error": f"Unable to read parquet file: {str(e)}"}

        try:
            session_history = self.get_recent_history(session_id, userid)
            query_response = self.build_query.get_sql_query(question, columns, session_history)
            query = query_response['sql_query']
            query_ = query.replace("parquet_data", f"parquet_scan('{parquet_path}')")
            print(query_)
            col_list = query_response['col_list']
            try:
                result = self.conn.execute(query_).fetchdf()
            except Exception as e:
                return {'status': f'kindly check datatype of {col_list}.there might be issue.'}
            result_dict = result.to_dict(orient='records')
            query_response['success'] = result_dict
            query_response['question'] = question
            timestamp = datetime.now().strftime("%d%m%y%H%M%S")

            connect, status = self.connection.connect_engine()
            query = f'''select * from "Session_Management" where "User_Id" = '{userid}' and "Session_Id"={session_id};'''
            df_, status = self.db_funct.fetch_data(query, connect)
            data_json = {timestamp: {"question": question, "answer": query_response}}
            if df_ is None or len(df_) == 0:
                try:
                    date_today = datetime.today().replace(microsecond=0)
                    log_entry = pd.DataFrame([{
                        "User_Id": userid, "Session_Id": session_id, "Session_Data": json.dumps(data_json),
                        "Created_On": date_today}])
                    status_post_data, status = self.db_funct.post_data(log_entry, "Session_Management", connect)
                except Exception as e:
                    return {'error': str(e)}, -1

            else:
                try:
                    data_json_str = json.dumps(data_json).replace("'", "''")
                    query = f"""UPDATE "Session_Management" SET "Session_Data" = "Session_Data" || '{data_json_str}'::jsonb
                                        WHERE "User_Id" = '{userid}' and "Session_Id"='{session_id}';"""
                    print(query)
                    status_update_data, status = self.db_funct.update_data(query, connect)
                    print('status', status)

                except Exception as e:
                    return {'error': str(e)}, -1
            if status == 1:
                query2 = f"""UPDATE "User_Session" SET "Flag" = 1 WHERE "User_Id"='{userid}' and "Session_Id"={session_id};"""
                status_create_account_, status_ = self.db_funct.update_data(query2, connect)
            discc = self.connection.disconnect_engine(connect)
            # sessions = read_sessions()
            # if str(session_id) not in sessions:
            #     return json.dumps({"error": "Session not found"},default=str), 404
            #
            # sessions[str(session_id)][timestamp] = {
            #         "question": question,"agent": query,"answer": query_response}
            # write_sessions(sessions)

            return json.dumps(query_response, default=str)
        except Exception as e:
            return {"error": str(e)}

    def get_insights(self, query_response):
        query_insight = self.build_query.get_query_insights(query_response)
        return query_insight