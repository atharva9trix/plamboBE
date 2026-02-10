import os

import duckdb
import pandas as pd

from src.file_handling.read_write_data import Readwrite
from src.db_connection.db_engine import Engine,Read_Write
class update_file:
    def __init__(self):
        self.conn=Engine()
        self.db_func = Read_Write()
        self.read_write = Readwrite()


    def create_atble(self,data):
        connect ,status= self.conn.connect_engine()
        print(connect)
        disconnect=self.conn.disconnect_engine(connect)
        print(disconnect)




if __name__=='__main__':
    a = update_file()
    data = 'd'

    v=a.create_atble(data)