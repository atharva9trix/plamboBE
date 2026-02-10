###this module only built for debuggin purpose nothing else

from src.tatvaAI.tatva_ai import TatvaAIMain
from src.data_description.data_types import DataDescribe

if __name__ == "__main__":
    tatva = TatvaAIMain()
    dd = DataDescribe()

    # user_session = tatva.get_user_session_id(1)
    # fetch_attr_dtype(self, file_path, user_id, session_id, sheet_name=0, connection=None):

    fdsfas = dd.fetch_attr_dtype()