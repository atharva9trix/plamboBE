import json
from datetime import datetime
import duckdb
import os,shutil
import pandas as pd
import yaml
from src.db_connection.db_engine import Engine,Read_Write
from functools import wraps
from src.controllers.update_parquet import update_file
from src.file_handling.read_write_data import Readwrite
from src.controllers.data_description import FetchDataType,Update_File
from src.data_analysis_dckdb.conversational_bi import AnalyticalFilter
with open('src/config/config.yml', 'r', encoding='utf8') as ymlfile:
    meta_data = yaml.load(ymlfile, Loader=yaml.FullLoader)

def db_connection(connect_method_name, disconnect_method_name):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            connect_method = getattr(self.connect, connect_method_name)
            disconnect_method = getattr(self.connect, disconnect_method_name)
            connection, _ = connect_method()
            print("Connected to DB")
            try:
                result = func(self, *args, connection=connection, **kwargs)
                return result
            except Exception as e:
                print("Error in decorated function:", e)
            finally:
                disconnect_method(connection)
                print("Disconnected from DB")
        return wrapper
    return decorator

class DataDescribe:
    def __init__(self):
        self.read_write = Readwrite()
        self.fetch_dtype = FetchDataType()
        self.std_all_file=meta_data["STD_ALL_FILE_PATH"]
        self.std_parquet_dir=meta_data["STD_PARQUET_PATH"]
        self.connect=Engine()
        self.update_col=update_file()
        self.db_func = Read_Write()
        self.update_file=Update_File()
        self.archive_all_file =meta_data["ARCHIVED_ALL_PATH"]
        self.archive_parquet_file = meta_data["ARCHIVED_PARQUET_PATH"]
        self.conv_bi=AnalyticalFilter()

    @db_connection('connect_engine','disconnect_engine')
    def fetch_attr_dtype(self,file_path,user_id, session_id, sheet_name=0,connection=None):
        query=f'''select * from "File_Name_Details" where "User_Session_Id" in ('{session_id}');'''
        df_, status = self.db_func.fetch_data(query, connection)
        if df_ is not None and len(df_)>0:
            msg = {'msg':f'''file is already present for this user_id: {user_id} and session_id: {session_id}.Do you want to update that file'''}
            return json.dumps(msg, default=str), 200
        else:
            pass
        try:
            user_session_id = session_id
            print('user_id',user_session_id)
            original_name = os.path.splitext(os.path.basename(file_path))[0]
            file_ext = os.path.splitext(os.path.basename(file_path))[1]
            new_filename = f"{user_id}_{session_id}_{original_name}{file_ext}"
            user_file_id = self.fetch_dtype.map_filenames(original_name,new_filename,user_session_id,connection)
            print('user_file_id',user_file_id)
            json_dict,new_path,df=self.fetch_dtype.fetch_json_dict(file_path,file_ext,sheet_name)
            print(json_dict)

            map_attribute = self.fetch_dtype.map_attribute_details(json_dict,user_file_id,connection)

            dest_file_path = os.path.join(self.std_all_file, new_filename)
            shutil.copy(new_path, dest_file_path)
            parquet_file_path = os.path.join(self.std_parquet_dir, f"{user_id}_{session_id}_{original_name}.parquet")
            df[df.select_dtypes('object').columns] = df.select_dtypes('object').apply(
                lambda x: x.str.lower())

            df.columns = df.columns.str.lower()
            df = df.apply(pd.to_numeric, errors='ignore')
            df = df.applymap(lambda x: ' '.join(x.strip().split()) if isinstance(x, str) else x)
            df.to_parquet(parquet_file_path, engine="fastparquet")

            try:
                unique_dict = {col: df[col].unique() for col in df.columns}
                unique_df = pd.DataFrame(dict([(k, pd.Series(v)) for k,v in unique_dict.items()]))
                output_dir = os.path.join("data", "parquet_unique_files")
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir,f"{user_id}_{session_id}_{original_name}.parquet")
                unique_df.to_parquet(output_path, engine='fastparquet')
            except:
                return {"msg": "unique data not save"}
            return {"success": map_attribute}
        except Exception as e:
            raise RuntimeError(f"Failed to process files: {e}")


    @db_connection('connect_engine','disconnect_engine')
    def updated_col_dtype(self, file_name,user_id,rename_col=None, update_dtype=None, connection=None):
        query = f'''SELECT "Updated_Filename" from "File_Name_Details" WHERE "User_Session_File_Id" = ('{user_id}');'''
        print(query)
        df, status = self.db_func.fetch_data(query, connection)
        new_name = df['Updated_Filename'][0]

        file_ext = os.path.splitext(os.path.basename(new_name))[1]
        parquet_name = new_name.replace(file_ext, ".parquet")
        parquet_path = os.path.join(self.std_parquet_dir, parquet_name)

        con = duckdb.connect()
        df = con.execute(f"SELECT * FROM read_parquet('{parquet_path}')").fetchdf()
        con.close()

        # updated_df = (df.rename(columns=rename_col) if rename_col else df).astype({k: v for k,v in
        #                 (update_dtype or {}).items() if k in df.columns})
        updated_df = df.rename(columns=rename_col) if rename_col else df
        # if update_dtype:
        #     updated_df,msg=self.fetch_dtype.handle_dtype(updated_df,update_dtype)
        # if update_dtype:
            # # Old Method (easy for regular datatype
            # datetime_cols = {k: v for k, v in update_dtype.items()
            #                  if v in ["datetime64[ns]", "datetime64","date"] and k in df.columns}
            # normal_cols = {k: v for k, v in update_dtype.items()
            #                if v not in ["datetime64[ns]", "datetime64"] and k in df.columns}
            # if normal_cols:
            #     try:
            #         df = df.astype(normal_cols)
            #     except Exception as e:
            #         failed_col = list(normal_cols.keys())[0]
            #         actual_dtype = df[failed_col].dtype
            #         return {"status": f"Column '{failed_col}' is {actual_dtype} and cannot be converted to {normal_cols[failed_col]}"}
            # for col in datetime_cols:
            #     try:
            #         df[col] = pd.to_datetime(df[col], errors="raise")
            #     except Exception as e:
            #         actual_dtype = df[col].dtype
            #         return {"status": f"Column '{col}' is {actual_dtype} and cannot be converted to {datetime_cols[col]}"}

        if update_dtype:
            ## New method handling Date, Time
            for k, v in update_dtype.items():
                try:
                    if v.__contains__('date'):
                        updated_df[k] = pd.to_datetime(updated_df[k], errors='coerce', infer_datetime_format=True)
                        print(f"Updated Datatype {k} -->> Date")
                    elif v.__contains__('time'):
                        updated_df[k] = pd.to_datetime(updated_df[k], errors='coerce', infer_datetime_format=True).dt.time
                        print(f"Updated Datatype {k} -->> time")
                    else:
                        if v in ['integer', 'float']:
                            df[k] = df[k].str.replace("[^0-9.\-n]", "", regex=True)
                            pd.to_numeric(updated_df[k], errors="coerce")
                        else:
                            updated_df[k] = updated_df[k].astype(v)

                        print(f"Updated Datatype {k} -->> {v}")
                except Exception as e:
                    return {"status": f"Column '{k}' datatype cannot be converted "}

        updated_df.to_parquet(parquet_path,engine="fastparquet")

        fetch_dtype_dict,df = self.fetch_dtype.fetch_col_dtpe_parquet(parquet_path)
        print(fetch_dtype_dict)
        date_today = datetime.today().replace(microsecond=0)
        query = f'''UPDATE "Attribute_Details" SET "Updated_Datatypes" =
                            '{fetch_dtype_dict}'::jsonb, "Modified_On"='{date_today}' WHERE "User_Session_File_Id" = '{user_id}';'''
        status_create_account, status = self.db_func.update_data(query, connection)

        if status==1:
            if isinstance(fetch_dtype_dict, str):
                fetch_dtype_dict = json.loads(fetch_dtype_dict)
            return {'status':fetch_dtype_dict}
        else:
            return {'status': 'failed to post data in attribute_details'}

    @db_connection('connect_engine','disconnect_engine')
    def replace_file_attributes(self,file_path,user_id, session_id, sheet_name=0,connection=None):
        try:
            move_file = self.update_file.move_files(user_id, session_id, self.std_all_file,self.std_parquet_dir,self.archive_all_file,self.archive_parquet_file)

            # user_sess_id,status=self.update_file.fetch_user_session_id(user_id,session_id,connection)
            # if status == -1:
            #     return {"msg":'failed to fetch user id from user_session'}

            original_name = os.path.splitext(os.path.basename(file_path))[0]
            file_ext = os.path.splitext(os.path.basename(file_path))[1]
            new_filename = f"{user_id}_{session_id}_{original_name}{file_ext}"

            user_file_id=self.update_file.update_file_name(original_name,new_filename,session_id,connection)

            json_dict, new_path, df = self.fetch_dtype.fetch_json_dict(file_path, file_ext, sheet_name)
            update_json=self.update_file.update_json_dict(json_dict,user_file_id,connection)
            dest_file_path = os.path.join(self.std_all_file, new_filename)
            shutil.copy(new_path, dest_file_path)

            parquet_file_path = os.path.join(self.std_parquet_dir, f"{user_id}_{session_id}_{original_name}.parquet")
            save_parquet = df.to_parquet(parquet_file_path, engine='fastparquet')
            return {"success": update_json}
        except Exception as e:
            return str(e)


if __name__=='__main__':
    a = DataDescribe()
    file = "data/sample_data.json"
    v = a.fetch_attr_dtype(file,10,18)
    print(v)
    # v=a.updated_col_dtype("R106 AUG",rename_col={"REVENUE":"rev"},update_dtype={"rev":"float64"})

