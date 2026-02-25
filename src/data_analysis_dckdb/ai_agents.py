import json
import os,re
from datetime import datetime
import duckdb
import pyarrow.parquet as pq
from pathlib import Path
from src.data_analysis_dckdb.conversational_bi import AnalyticalFilter
# Session read/write functions
SESSION_FILE = Path("sessions.json")
if not SESSION_FILE.exists():
    SESSION_FILE.write_text(json.dumps({}))
BASE_DIR = Path(__file__).resolve().parents[2] / "data" / "parquet_files"
def read_sessions():
    with open(SESSION_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def write_sessions(data):
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f, indent=4)


def fix_sql_columns(sql_query, parquet_path):
    """
    Automatically replace incorrect or underscored column names in SQL
    with the actual column names found in the Parquet file.
    """
    try:
        cols = duckdb.sql(f"SELECT * FROM parquet_scan('{parquet_path}') LIMIT 1").df().columns
        col_map = {c.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("%", "percent"): c for c in
                   cols}

        # Replace normalized names with actual ones in the SQL
        for norm, actual in col_map.items():
            # Replace only unquoted names that match normalized ones
            pattern = rf'\b{norm}\b'
            sql_query = re.sub(pattern, f'"{actual}"', sql_query)
        return sql_query
    except Exception as e:
        print(f"⚠️ Column fixer failed: {e}")
        return sql_query

# ==========================
# Session Manager Agent
# ==========================
class SessionManager:
    def __init__(self, read_func=read_sessions, write_func=write_sessions):
        self.read = read_func
        self.write = write_func
        self.analytica_filter=AnalyticalFilter()
        self.conn = duckdb.connect(database=":memory:")

    def save_entry(self, session_id, question, query, result_dict, query_response=None):
        sessions = self.read()
        timestamp = datetime.now().strftime("%d%m%y%H%M%S")
        if str(session_id) not in sessions:
            sessions[str(session_id)] = {}
        sessions[str(session_id)][timestamp] = {
            "question": question,
            "agent": query,
            "query_metadata": query_response,
            "answer": {"success": result_dict},
        }
        self.write(sessions)

    def get_recent_history(self, session_id, n=5):
        sessions = self.read()
        if str(session_id) not in sessions:
            return []
        conv = sessions[str(session_id)]
        keys = sorted(conv.keys())[-n:]
        return [(conv[k]["question"], conv[k]["answer"]) for k in keys]


# ==========================
# Query Validator Agent
# ==========================
class QueryValidatorAgent:
    def __init__(self, valid_columns):
        self.valid_columns = [c.lower() for c in valid_columns]

    def run(self, sql_query):
        if not sql_query.strip().lower().startswith("select"):
            return {"valid": False, "reason": "Query must start with SELECT."}

        if ";" not in sql_query:
            return {"valid": False, "reason": "Query must end with a semicolon."}

        forbidden = ["drop", "delete", "alter", "update", "insert"]
        if any(word in sql_query.lower() for word in forbidden):
            return {"valid": False, "reason": "Query contains forbidden operations."}

        return {"valid": True}


# ==========================
# Query Executor Agent
# ==========================
class QueryExecutorAgent:
    def __init__(self, conn):
        self.conn = duckdb.connect(database=":memory:")
    def run(self, sql_query, col_list):
        try:
            df = self.conn.execute(sql_query).fetchdf()
            if df.empty:
                return {"status": "no_data", "data": None}
            return {"status": "success", "data": df}
        except Exception as e:
            return {"status": "error", "data": None, "error": f"Check datatype of {col_list}: {str(e)}"}


# ==========================
# Conversation Agent
# ==========================
class ConversationAgent:
    def __init__(self, session_manager, base_dir):
        """
        analytical_filter: instance of AnalyticalFilter class
        session_manager: instance of SessionManager
        base_dir: base directory where parquet files are stored
        conn: duckdb connection
        """
        self.session_manager = session_manager
        self.base_dir = base_dir
        self.analytical_filter = AnalyticalFilter()
        self.conn = duckdb.connect(database=":memory:")


    def handle_question(self, userid, session_id, question, filename):
        # ---- Step 1: Load parquet and columns
        parquet_path = os.path.join(self.base_dir,f'''{userid}_{session_id}_{filename}.parquet''' )
        if not os.path.exists(parquet_path):
            return {"reply": "⚠️ File not found. Please re-upload.", "status": "error"}

        try:
            parquet_file = pq.ParquetFile(parquet_path)
            columns = parquet_file.schema.names
        except Exception as e:
            return {"reply": f"Unable to read parquet file: {e}", "status": "error"}

        # ---- Step 2: Generate query using AnalyticalFilter
        query_response = self.analytical_filter.get_sql_query_1(question, columns)
        sql_query = query_response["sql_query"]
        print(sql_query)
        sql_query_full = sql_query.replace("parquet_data", f"parquet_scan('{parquet_path}')")

        # ---- Step 3: Validate query
        validator = QueryValidatorAgent(columns)
        validation = validator.run(sql_query)
        if not validation["valid"]:
            return {
                "reply": f"❌ Query invalid: {validation['reason']}. Try a different question?",
                "status": "invalid_query"
            }

        # ---- Step 4: Execute query
        sql_query_full_fixed = fix_sql_columns(sql_query_full, parquet_path)
        executor = QueryExecutorAgent(self.conn)
        exec_result = executor.run(sql_query_full_fixed, query_response.get("col_list", []))

        if exec_result["status"] == "no_data":
            return {"reply": "No data found for this query. Try another question?", "status": "no_data"}

        if exec_result["status"] == "error":
            return {"reply": exec_result["error"], "status": "execution_error"}

        # ---- Step 5: Save session
        self.session_manager.save_entry(session_id, question, sql_query_full_fixed, exec_result["data"].to_dict(orient="records"))

        # ---- Step 6: Return result
        return {
            "reply": "Query executed successfully.",
            "data": exec_result["data"].to_dict(orient="records"),**query_response,
            "status": "success"
        }

if __name__ == "__main__":
    conn = duckdb.connect()
    session_manager = SessionManager()
    base_dir = "data/parquet_files"

    convo_agent = ConversationAgent(session_manager, BASE_DIR)
    response = convo_agent.handle_question(userid=1, session_id=7, question="For each Advisor, show:total clients handled",
                                           filename="finance")
    print(json.dumps(response, indent=4))
