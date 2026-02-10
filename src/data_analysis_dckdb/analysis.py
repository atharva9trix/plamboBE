import duckdb,os
import json

import pandas as pd
import pyarrow.parquet as pq
import yaml
from datetime import datetime
from pathlib import Path
from src.data_analysis_dckdb.conversational_bi import AnalyticalFilter
from src.controllers.data_analysis import DataAnalysis
from src.db_conenct.db_engine import Engine,Read_Write
with open('src/config/config.yml', 'r', encoding='utf8') as ymlfile:
    meta_data = yaml.load(ymlfile, Loader=yaml.FullLoader)

SESSION_FILE = Path("sessions.json")
if not SESSION_FILE.exists():
    SESSION_FILE.write_text(json.dumps({}))
def read_sessions():
    with open(SESSION_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def write_sessions(data):
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f, indent=4)


class DuckdbAnalysis:
    def __init__(self):
        self.base_dir = meta_data["STD_PARQUET_PATH"]
        self.conn = duckdb.connect(database=":memory:")
        self.analysis = DataAnalysis()
        self.build_query = AnalyticalFilter()
        self.db_funct = Read_Write()
        self.connection = Engine()


    def query_analysis(self, userid, session_id, question,filename):
        parquet_path = self.analysis.get_parquet_path(self.base_dir,userid, session_id,filename)
        if not os.path.exists(parquet_path):
            return {"error": "File not found"}
        try:
            parquet_file = pq.ParquetFile(parquet_path)
            print(parquet_file)
            columns = parquet_file.schema.names
        except Exception as e:
            return {"error": f"Unable to read parquet file: {str(e)}"}
        try:
            session_history=self.get_recent_history(session_id,userid)
            query_response=self.build_query.get_sql_query(question,columns,session_history)
            query = query_response['sql_query']
            query_ = query.replace("parquet_data", f"parquet_scan('{parquet_path}')")
            print(query_)
            col_list = query_response['col_list']
            try:
                result = self.conn.execute(query_).fetchdf()
            except Exception as e:
                return {'status':f'kindly check datatype of {col_list}.there might be issue.'}
            result_dict=result.to_dict(orient='records')
            query_response['success'] = result_dict
            query_response['question'] = question
            timestamp = datetime.now().strftime("%d%m%y%H%M%S")

            connect,status = self.connection.connect_engine()
            query = f'''select * from "Session_Management" where "User_Id" = {userid} and "Session_Id"={session_id};'''
            df_, status = self.db_funct.fetch_data(query, connect)
            data_json={timestamp:{"question": question,"answer": query_response}}
            if df_ is None or len(df_) == 0:
                try:
                    date_today = datetime.today().replace(microsecond=0)
                    log_entry = pd.DataFrame([{
                        "User_Id":userid, "Session_Id":session_id,"Session_Data":json.dumps(data_json),"Created_On":date_today}])
                    status_post_data, status = self.db_funct.post_data(log_entry, "Session_Management", connect)
                except Exception as e:
                    return {'error':str(e)},-1

            else:
                try:
                    data_json_str = json.dumps(data_json).replace("'", "''")
                    query = f"""UPDATE "Session_Management" SET "Session_Data" = "Session_Data" || '{data_json_str}'::jsonb
                                        WHERE "User_Id" = '{userid}' and "Session_Id"='{session_id}';"""
                    print(query)
                    status_update_data, status = self.db_funct.update_data(query, connect)
                    print('status',status)

                except Exception as e:
                    return {'error':str(e)},-1
            if status == 1:
                query2 = f"""UPDATE "User_Session" SET "Flag" = 1 WHERE "User_Id"={userid} and "Session_Id"={session_id};"""
                status_create_account_, status_ = self.db_funct.update_data(query2, connect)
            discc = self.connection.disconnect_engine(connect)
            # sessions = read_sessions()
            # if str(session_id) not in sessions:
            #     return json.dumps({"error": "Session not found"},default=str), 404
            #
            # sessions[str(session_id)][timestamp] = {
            #         "question": question,"agent": query,"answer": query_response}
            # write_sessions(sessions)

            return json.dumps(query_response,default=str)
        except Exception as e:
            return {"error": str(e)}


    def get_insights(self,query_response):
        print(query_response)
        query_insight = self.build_query.get_query_insights(query_response)
        print(query_insight)
        return query_insight

    def get_recent_history(self, session_id,user_id, n=5):
        connect, status = self.connection.connect_engine()
        query = f'''select "Session_Data" from "Session_Management"
                where "User_Id"={user_id} and "Session_Id"={session_id};'''
        df_, status = self.db_funct.fetch_data(query, connect)
        if len(df_)>0:
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
        disconnect=self.connection.disconnect_engine(connect)
        return result_dict


if __name__=='__main__':
    a=DuckdbAnalysis()
    # query ='''SELECT month,year,sum(amount) as amount,
    #         sum(volume) as volume,
    #         sum(amount)/sum(volume) as asp,
    #         ((SUM(amount) / NULLIF(SUM(total_purchase_price), 0)) - 1) * 100 AS margin,
    #         SUM(amount) / NULLIF(COUNT(Distinct(bill_no)), 0) as abv
    #          FROM parquet_data GROUP BY month,year order by month;'''

    # question = 'what is average amount of salesman POOJA NINORE'
    # v=a.query_analysis(1,17,question,filename='khandelwal_test_data1.parquet')
    v=a.get_recent_history(user_id=2,session_id=15)
    print(v)
