import os
import pandas as pd
# import polars as pl
import json

class Readwrite:
    def read_data(self, filepath, engine, **kwargs):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"the file {filepath}does not exist")

        file_extension = os.path.splitext(filepath)[-1].lower()
        supported_extension = ['.csv', '.txt', '.xls', '.xlsx', '.xlsm', '.json']
        if file_extension not in supported_extension:
            raise ValueError(f"{file_extension} is not supported.use another extension in {supported_extension}.")

        supported_engine = ['open', 'pandas', 'polars']
        if engine not in supported_engine:
            raise ValueError(f"engine {engine} not supported.use one of {supported_engine}.")
        try:
            if engine == 'open':
                if filepath.endswith('.txt') or filepath.endswith('.csv'):
                    file = open(filepath, 'r')
                    data = file.read()
                    return data

                elif filepath.endswith('.json'):
                    with open(filepath, 'r') as file:
                        data = json.load(file)
                        print(data)
                else:
                    print(f"{filepath}not supported")

            elif engine == 'pandas':
                import pandas as pd
                df = pd.DataFrame()
                if filepath.endswith('.csv') or filepath.endswith('.txt'):
                    df = pd.read_csv(filepath, **kwargs)
                elif filepath.endswith('.xls') or filepath.endswith('.xlsx') or filepath.endswith('.xlsm'):
                    df = pd.read_excel(filepath, **kwargs)
                elif filepath.endswith('.json'):
                    df = pd.read_json(filepath, **kwargs)
                elif filepath.endswith('.parquet'):
                    df = pd.read_parquet(filepath,**kwargs)
                return df

            # elif engine == 'polars':
            #     df=pl.DataFrame()
            #     if filepath.endswith('.csv') or filepath.endswith('.txt'):
            #         df = pl.read_csv(filepath)
            #     elif filepath.endswith('.xlsx') or filepath.endswith('.xls') or filepath.endswith('.xlsm'):
            #         df = pl.read_excel(filepath)
            #     elif filepath.endswith('.json'):
            #         df = pl.read_json(filepath)
            #     return df
        except:
            raise ValueError(f"{filepath} is not read using engine{engine}")

    def write_data(self,data,filepath,engine,**kwargs):

        file_extension=os.path.splitext(filepath)[-1].lower()
        supported_extension=['.csv','.txt','.xlsx','.xlsm','.xls','.json']
        if file_extension not in supported_extension:
            raise ValueError(f"{file_extension} not supported.use one of{supported_extension}")
        supported_engine=['pandas','polars','open']
        if engine not in supported_engine:
            raise ValueError(f"engine{engine} not supported.use one of {supported_engine}")
        try:
            if engine=='pandas':
                if filepath.endswith('.csv') or filepath.endswith('.txt'):
                 df=pd.DataFrame(data)
                 df.to_csv(filepath,**kwargs)
                elif filepath.endswith('.xlsx') or filepath.endswith('.xlsm') or filepath.endswith('.xls'):
                 df=pd.DataFrame(data)
                 df.to_excel(filepath,**kwargs,index=False)
                elif filepath.endswith('.json'):
                 df=pd.DataFrame(data)
                 df.to_json(filepath,**kwargs)
                return data
            # elif engine=='polars':
            #     if filepath.endswith('.csv') or filepath.endswith('.txt'):
            #         df=pl.DataFrame(data)
            #         df.write_csv(filepath,**kwargs)
            #     elif filepath.endswith('.xlsx') or filepath.endswith('.xlsm') or filepath.endswith('.xls'):
            #         df=pl.DataFrame(data)
            #         df.write_excel(filepath,**kwargs)
            #     elif filepath.endswith('.json'):
            #         df=pl.DataFrame(data)
            #         df.write_json(filepath)
            #     return data
        except:
            raise ValueError(f"could not write file {filepath} with {engine} ")