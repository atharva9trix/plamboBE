import re
from _datetime import datetime
from functools import wraps
import numpy as np
import pandas as pd, os, json, csv
import pyarrow.parquet as pq
import shutil,glob
from src.db_connection.db_engine import Engine,Read_Write
from pandas.api.types import infer_dtype
from src.file_handling.read_write_data import Readwrite

def db_connection(connect_method_name, disconnect_method_name):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            connect_method = getattr(self.connection, connect_method_name)
            disconnect_method = getattr(self.connection, disconnect_method_name)
            connection, _ = connect_method()
            print("Connected to DB")
            try:
                result = func(self, *args, connection=connection, **kwargs)
                return result
            finally:
                disconnect_method(connection)
                print("Disconnected from DB")
        return wrapper
    return decorator


class FetchDataType:
    def __init__(self):
        self.read_write = Readwrite()
        self.connection = Engine()
        self.db_func = Read_Write()

    def fetch_col_dtype_excel(self,file_path,sheet_name=0):
        df = self.read_excel(file_path,sheet_name)

        descriptive_data_types = {}
        for col in df.columns:
            series = df[col]
            if pd.api.types.is_integer_dtype(series):
                dtype = "integer"
            elif pd.api.types.is_float_dtype(series):
                dtype = "float"
            elif pd.api.types.is_datetime64_any_dtype(series):
                dtype = "datetime"
            elif pd.api.types.is_categorical_dtype(series):
                dtype = "category"
            elif pd.api.types.is_bool_dtype(series):
                dtype = "boolean"
            elif pd.api.types.is_timedelta64_dtype(series):
                dtype = "timedelta"
            elif pd.api.types.is_object_dtype(series):
                if series.dropna().map(type).eq(str).all():
                    dtype = "string"
                else:
                    dtype = "string"
            else:
                dtype = "other"
            descriptive_data_types[col]=dtype
        json_dict = json.dumps(descriptive_data_types,default=str)
        return json_dict,df

    def read_excel(self,filepath,sheetname):
        try:
            df = pd.read_excel(filepath, sheet_name=sheetname, header=None)
            first_row_non_null = df.iloc[0].notna().sum()
            total_cols = df.shape[1]
            filled_ratio = first_row_non_null / total_cols

            if filled_ratio >= 0.9:
                data = pd.read_excel(filepath, sheet_name=sheetname)
            else:
                threshold = int(total_cols * 0.9)
                df1 = df.dropna(thresh=threshold).reset_index(drop=True)

                header_row_index = df1.notna().sum(axis=1).idxmax()
                columns = df1.iloc[header_row_index].tolist()

                data = df1.iloc[header_row_index + 1:].reset_index(drop=True)
                data.columns = columns

        except Exception as e:
            data = pd.read_excel(filepath, sheet_name=sheetname)

        return data

    # df = pd.read_excel(filepath, sheet_name=sheetname, header=None)
    # threshold = int(df.shape[1] * 0.8)
    # df1 = df.dropna(thresh=threshold).reset_index(drop=True)
    # header_row_index = df1.notna().sum(axis=1).idxmax()
    # if header_row_index == 0:
    #     data = pd.read_excel(filepath, sheet_name=sheetname)
    # else:
    #     columns = df1.iloc[header_row_index].tolist()
    #     data = df1.iloc[header_row_index:].reset_index(drop=True)
    #     data.columns = columns



    def save_parquet(self,file_path,parquet_file_path,file_ext,sheetname=0,engine=None):
        try:
            if file_ext.lower() in [".xlsm", ".xlsx"]:
                df=pd.read_parquet(parquet_file_path,engine='pyarrow')
                #df = self.read_write.read_data(file_path, sheet_name=sheetname, engine='pandas')
                df.to_parquet(parquet_file_path, index=False, engine='fastparquet')

            elif file_ext == ".parquet":
                shutil.copy(file_path, parquet_file_path)

            elif file_ext in ['.csv','.txt']:
                df = self.fetch_df_csv(file_path)
                df.to_parquet(parquet_file_path, index=False, engine='fastparquet')

            else:
                return {'status': 'failed', 'message': 'Unsupported file type'}, 0

            return {'status':'successfully converted the file to parquet'}, 1
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}

    def map_attribute_details(self,json_dict,user_file_id,connection=None):
        date_today = datetime.today().replace(microsecond=0)
        log_entry = pd.DataFrame([{
            "User_Session_File_Id": user_file_id, "Data_Types": json_dict,
            "Status":'active',"Created_On":date_today}])
        status_create_account, status = self.db_func.post_data(log_entry, "Attribute_Details", connection)

        # query = f'''UPDATE "Attribute_Details" SET "Data_Types" =
        #             '{json_dict}'::jsonb WHERE "User_Session_File_Id" = '{user_file_id}';'''
        # print(query)
        # status_create_account,status = self.db_func.update_data(query,connection)
        if status == 1:
            log_entry["Data_Types"] = log_entry["Data_Types"].apply(json.loads)
            return log_entry.to_dict(orient='records')
        else:
            return {'status': 'failed to post data in attribute_details'}


    def fetch_col_dtpe_parquet(self,file_path):
        df=pd.read_parquet(file_path)
        schema = pq.read_schema(file_path)
        schema_dict = {name: str(schema.field(name).type) for name in schema.names}
        json_dict = json.dumps(schema_dict, default=str)
        return json_dict,df

    def fetch_col_dtype_csv(self,file_path):
        df=self.fetch_df_csv(file_path)
        obj_cols = df.select_dtypes(include=["object"]).columns
        df[obj_cols] = df[obj_cols].apply(
            lambda col: pd.to_datetime(col, errors="ignore"))
        df = df.convert_dtypes()
        dtype_mapping = {
            "string": "string",
            "Int64": "integer",
            "Float64": "float",
            "boolean": "boolean",
            "datetime64[ns]": "datetime"}
        cols_and_dtypes = df.dtypes.astype(str).map(dtype_mapping).to_dict()

        json_dict = json.dumps(cols_and_dtypes, default=str)
        return json_dict,df

    def fetch_delimiter(self,file_path):
        encoding_list = ["utf-8", "utf-16", "latin-1"]
        common_delimiters = [",", "|", "\t", ";", ":"]
        for enc in encoding_list:
            try:
                with open(file_path, "r", encoding=enc,errors='ignore') as f:
                    sample = f.read(4096)
                    f.seek(0)
                    try:
                        dialect = csv.Sniffer().sniff(sample, delimiters="".join(common_delimiters))
                        delimiter = dialect.delimiter
                    except csv.Error:
                        # delimiter = max(common_delimiters, key=sample.count)
                        counts = {d: sample.count(d) for d in common_delimiters}
                        delimiter = max(counts, key=counts.get)
                        if all(v == 0 for v in counts.values()):
                            header_line = sample.splitlines()[0]
                            # keep only non-alphanumeric symbols
                            symbols = re.findall(r"[^A-Za-z0-9\s]", header_line)
                            if symbols:
                                delimiter = symbols[0]  # assume first special symbol
                            else:
                                delimiter = "whitespace"
                    return delimiter
            except Exception as e:
                return e

    def map_filenames(self,old_name,new_name,user_sessin_id,connection=None):
        date_today = datetime.today().replace(microsecond=0)
        log_entry = pd.DataFrame([{
            "File_Name": old_name, "Updated_Filename": new_name,"User_Session_Id":user_sessin_id,
            "Status":'active',"Created_On":date_today}])

        status_create_account, status = self.db_func.post_data(log_entry, "File_Name_Details", connection)
        if status==1:
            query = f'''SELECT "User_Session_File_Id" from "File_Name_Details" WHERE "User_Session_Id" = ('{user_sessin_id}')'''
            df, status = self.db_func.fetch_data(query, connection)
            user_file_id = df['User_Session_File_Id'][0]
            return user_file_id
        else:
            return {'status': 'failed to post data in File_Name_Details table'}

    def map_user_session(self,user_id,session_id,connection=None):
        # date_today = datetime.today().replace(microsecond=0)
        # log_entry = pd.DataFrame([{
        #     "User_Id": user_id, "Session_Id": session_id,"Created_On":date_today,"Status":'active'}])
        #
        # status_create_account, status = self.db_func.post_data(log_entry, "User_Session", connection)
        # if status==1:
        try:
            query = f'''SELECT "User_Session_Id" from "User_Session" WHERE "User_Id" = ('{user_id}') and "Session_Id"= ('{session_id}')'''
            df, status = self.db_func.fetch_data(query, connection)
            user_sess_id = df['User_Session_Id'][0]
            print('user_id',user_sess_id)
            return user_sess_id
        except:
            return {'status': 'failed to post data in User_Session'}

    def fetch_df_csv(self,file_path):
        delimiter = self.fetch_delimiter(file_path)
        if delimiter == "whitespace":
            df = pd.read_csv(file_path, sep=r"\s+", engine="python")
            if df.shape[1] == 1:
                df = pd.read_fwf(file_path)
        else:
            df = pd.read_csv(file_path, sep=delimiter)
        return df

    def fetch_json_dict(self,file_path,file_ext,sheet_name):
        try:
            json_dict = {}
            new_path = file_path
            if file_ext == ".paraquet":
                file_ext = ".parquet"
                new_path = file_path.replace(".paraquet", ".parquet")

            handler_map = {
                ".xlsx": lambda p: self.fetch_col_dtype_excel(p, sheet_name),
                ".xlsm": lambda p: self.fetch_col_dtype_excel(p, sheet_name),
                ".parquet": self.fetch_col_dtpe_parquet,
                ".csv": self.fetch_col_dtype_csv,
                ".txt": self.fetch_col_dtype_csv,
                ".json": self.get_json_schema,}

            if file_ext in handler_map:
                json_dict, df = handler_map[file_ext](new_path)

            return json_dict, new_path, df

        except Exception as e:
            return e

        #     if file_ext in ['.xlsx', '.xlsm']:
        #         json_dict,df= self.fetch_col_dtype_excel(new_path, sheet_name)
        #
        #     elif file_ext in ['.parquet', '.paraquet']:
        #         if file_ext == '.paraquet':
        #             new_path = file_path.replace(".paraquet", ".parquet")
        #         json_dict,df= self.fetch_col_dtpe_parquet(new_path)
        #
        #     elif file_ext in ['.csv', '.txt']:
        #         json_dict,df = self.fetch_col_dtype_csv(new_path)
        #     elif file_ext =='.json':
        #         json_dict,df=self.get_json_schema(new_path)
        #     return json_dict, new_path,df
        # except Exception as e:
        #     return e

    def infer_type(self,value):
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            try:
                pd.to_datetime(value, errors="raise")
                return "date"
            except Exception:
                return "string"
        elif value is None:
            return "null"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        return "unknown"

    def flatten_json(self,obj, parent_key=""):
        schema = {}
        if isinstance(obj, dict):
            for k, v in obj.items():
                full_key = f"{parent_key}.{k}" if parent_key else k
                if isinstance(v, (dict, list)):
                    schema.update(self.flatten_json(v, full_key))
                else:
                    schema[full_key] = self.infer_type(v)

        elif isinstance(obj, list):
            if obj:  # check first element
                schema.update(self.flatten_json(obj[0], parent_key))
            else:
                schema[parent_key] = "array(empty)"
        else:
            schema[parent_key] = self.infer_type(obj)
        return schema

    def get_json_schema(self,file_path):
        with open(file_path, "r") as f:
            data = json.load(f)

        if isinstance(data, list) and data:
            dict=self.flatten_json(data[0])
            df = pd.DataFrame(data)
            return json.dumps(dict,default=str),df

        else:
            dict=self.flatten_json(data)
            df = pd.DataFrame(data)
            return json.dumps(dict,default=str),df

    # def handle_dtype(self,df,update_dtype):
    #     try:
    #         datetime_cols = {k: v for k, v in update_dtype.items()
    #                          if v in ["datetime64[ns]", "datetime64"] and k in df.columns}
    #         normal_cols = {k: v for k, v in update_dtype.items()
    #                        if v not in ["datetime64[ns]", "datetime64"] and k in df.columns}
    #
    #         if normal_cols:
    #             df = df.astype(normal_cols)
    #
    #         for col in datetime_cols:
    #                 df[col] = pd.to_datetime(df[col], errors="raise")
    #     except Exception as e:
    #         return None, f"Column '{col}' could not be converted to {update_dtype[col]}: {str(e)}"
    #
    # return df, "All conversions applied successfully" if update_dtype else df


class Update_File:
    def __init__(self):
        self.read_write = Readwrite()
        self.connection = Engine()
        self.db_func = Read_Write()
    def fetch_user_session_id(self,user_id,session_id,connection):
        query = f'''SELECT "User_Session_Id" from "User_Session" WHERE "User_Id" = ('{user_id}') and "Session_Id"= ('{session_id}')'''
        df, status = self.db_func.fetch_data(query, connection)
        user_sess_id = df['User_Session_Id'][0]
        return user_sess_id,status

    def update_file_name(self,original_name,new_filename,user_sess_id,connection):
        query = f'''UPDATE "File_Name_Details" SET "File_Name" ='{original_name}',
                        "Updated_Filename"='{new_filename}' WHERE "User_Session_Id" = '{user_sess_id}';'''
        print(query)
        status_create_account, status = self.db_func.update_data(query, connection)
        if status==1:
            query = f'''SELECT "User_Session_File_Id" from "File_Name_Details" WHERE "User_Session_Id" = ('{user_sess_id}')'''
            df, status = self.db_func.fetch_data(query, connection)
            user_file_id = df['User_Session_File_Id'][0]
            return user_file_id
        else:
            return 'failed to update data in File_Name_Details'

    def update_json_dict(self,json_dict,user_file_id,connection):
        query = f'''UPDATE "Attribute_Details" SET "Data_Types" =
                            '{json_dict}'::jsonb WHERE "User_Session_File_Id" = '{user_file_id}';'''
        print(query)
        status_create_account, status = self.db_func.update_data(query, connection)
        if status==1:
            log_entry = pd.DataFrame([{
                "User_Session_File_Id": user_file_id, "Data_Types": json_dict}])
            log_entry["Data_Types"] = log_entry["Data_Types"].apply(json.loads)
            return log_entry.to_dict(orient='records')
        else:
            return 'failed to update json_dict in Attribute_Details'

    def move_files(self,user_id, session_id, all_file_path, parquet_file_path, archived_all_file_path,archived_parquet_file_path):
        os.makedirs(archived_all_file_path, exist_ok=True)
        os.makedirs(archived_parquet_file_path, exist_ok=True)

        pattern = f"{user_id}_{session_id}_*"
        all_files = glob.glob(os.path.join(all_file_path, pattern))
        parquet_files = glob.glob(os.path.join(parquet_file_path, pattern))

        [shutil.move(f, os.path.join(archived_all_file_path, os.path.basename(f))) for f in all_files]
        [shutil.move(f, os.path.join(archived_parquet_file_path, os.path.basename(f))) for f in parquet_files]

        if not all_files and not parquet_files:
            return f"No files found for {user_id}_{session_id}", -1
        else:
            return f"Moved {len(all_files)} from all_file and {len(parquet_files)} from parquet_file.", 1


if __name__=='__main__':
    a=FetchDataType()
    v=a.get_json_schema("C:/Users/Asus/Downloads/sample_data.json")

