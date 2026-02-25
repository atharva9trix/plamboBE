from datetime import datetime
import json
import pandas as pd
from src.db_connection.db_engine import Engine,Read_Write


class CRUD_Operations:

    def __init__(self):
      self.connection = Engine()
      self.db_funct = Read_Write()

    def create(self,payload, level):
        ## establish connection with DBs
        connect,status = self.connection.connect_engine()
        date_today = datetime.today().replace(microsecond=0)
        status = "active"
        payload["Status"] = status
        payload["Created_On"] = date_today
        print(payload, "this is payload data")
        
        if level.lower() == "client":
            print("level is client")
            payload_df = pd.DataFrame([payload])
            print(payload_df)
            status_post_data, status = self.db_funct.post_data(payload_df, "Client", connect)
            print(status_post_data, status, "this is post data statys ")
            if status == 1:
                return f'Client {payload["Client_Name"]} is registered successflly'
            else:
                return status_post_data
            
        elif level.lower() == "project":
        
            client_name = payload["Client_Name"]
            payload.pop("Client_Name")
            get_client_name_query = f'''SELECT "Id" as "Client_Id" from "Client" WHERE "Client_Name" = '{client_name}' '''
            print(get_client_name_query, "this is fetch client id query from cleint table")
            df_, status = self.db_funct.fetch_data(get_client_name_query, connect)
            
            if len(df_) == 0:
                return f"client {client_name} is not registered"
                
            client_id = df_["Client_Id"].tolist()[0]
            
            payload["Client_Id"] = client_id
            print(client_id, "this is client id fetch from cleint table")
            payload_df = pd.DataFrame([payload])
            print(payload_df)
            status_post_data, status = self.db_funct.post_data(payload_df, "Project", connect)
            #print(status_post_data, status, "this is post data statys of project")
            if status == 1:
                return f'Project {payload["Project_Name"]} is registered successflly'
            else:
                return status_post_data
            
        else:
            return "this is not a valid level"
        
        print(0)
        
    
    def get(self, payload, level):
        connect,status = self.connection.connect_engine()
        if level.lower() == "client":
            select_query = f'''Select "Id","Client_Name"  from "{level.title()}";'''
            print(select_query)
            df_, status = self.db_funct.fetch_data(select_query, connect)
            if status ==1:
                
#                level_names_ls = (
#                                  df_[f"{level.title()}_Name"]
#                                  .astype(str)
#                                  .str.title()
#                                  .tolist()
#                                  )
                #print(level_names_ls)
                #print(df_)
                return json.dumps(df_.to_dict(orient = 'records'), default = str)
                
        elif level.lower() == "project":
            cl_name = payload["Client_Name"]
            cl_id_query = f'''Select "Id" from "Client" Where "Client_Name" = '{cl_name}';'''
            cl_id_df_, status_clid = self.db_funct.fetch_data(cl_id_query, connect)
            if status_clid != 1:
                return f"{cl_name} client is not registered"
                
            cl_id = cl_id_df_["Id"].tolist()[0]
        
            select_query = f'''Select "Id","Project_Name" from "{level.title()}" where "Client_Id" = {cl_id};'''
            df_, status = self.db_funct.fetch_data(select_query, connect)
            if status == 1:
                
#                level_names_ls = (
#                                  df_[f"{level.title()}_Name"]
#                                  .astype(str)
#                                  .str.title()
#                                  .tolist()
#                                  )
#                print(level_names_ls)
                #print(df_)
                return json.dumps(df_.to_dict(orient = 'records'), default = str) 
            
        else:
            return f"Failed to fetch list of {level}s"
    
        