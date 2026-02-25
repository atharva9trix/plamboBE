###this module only built for debuggin purpose nothing else

from src.tatvaAI.tatva_ai import TatvaAIMain
from src.data_description.data_types import DataDescribe
from src.validators.query_validator import QueryValidator
from src.crud_ops.crud_operations import CRUD_Operations
from src.generator_agent.agent import MediaAgent

if __name__ == "__main__":
    tatva = TatvaAIMain()
    dd = DataDescribe()
    qv = QueryValidator()
    payload = {"Client_Name":"Client4"}
    #val = qv.validate(payload)
    crud_obj = CRUD_Operations()
    ma = MediaAgent()
    
    payload = {"Client_Name":"Client4"}
    
    #aa = ma.generate(payload)  
    
    create_respones = crud_obj.get(payload, level = "project")
    print(create_respones)
    

    # user_session = tatva.get_user_session_id(1)
    # fetch_attr_dtype(self, file_path, user_id, session_id, sheet_name=0, connection=None):

    #fdsfas = dd.fetch_attr_dtype()