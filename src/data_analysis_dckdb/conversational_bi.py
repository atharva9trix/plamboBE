import datetime, time, re
from datetime import datetime
# from langchain_community.llms import Ollama
# from langchain.chains import ConversationChain
# from langchain.memory import ConversationBufferMemory
# from langchain_ollama import OllamaLLM
import ast
import yaml
import pyarrow.parquet as pq
import json
import requests
# import ollama
from google import genai
from google.genai import types

# with open('src/config/config.yml', 'r', encoding='utf8') as ymlfile:
#     meta_data = yaml.load(ymlfile, Loader=yaml.FullLoader)


class AnalyticalFilter:

    def __init__(self):
        self.api_counter = 0
        self.api_limit = 250

        ### APIS -- [Sam Navaantrix, Sam Personal]
        self.api_keys = []  ##
        # self.client = genai.Client(
        #    api_key=self.api_key,)

        self.generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=-1, ),
            response_mime_type="text/plain", )
        self.model = "gemini-2.5-flash"

        # self.util = util.MasterData()
        # self.calc = util.MasterCalc()
        # self.dash_obj = dashboard_main_v2.AnalyticalFilter()
        # self.output_path = meta_data["OUTPUT_DATA_PATH"]

        self.VECTOR_KEYWORDS = [
            "sales",
            "amount",
            "margin",
            "asp",
            "abv",
            "rooms",
            "occupancy"]
        self.attrs = ['industry', 'customer', 'branch_name', 'brand', 'lob', 'bill_no', 'date', 'product', 'salesman',
                      'category', 'subcategory', 'subcategory', 'groupfortax', 'saletype', 'area', 'state', 'city',
                      'verticle']

    def _get_api_key_client(self):
        index = (self.api_counter // self.api_limit) % len(self.api_keys)
        api_ = self.api_keys[index]
        client = genai.Client(
            api_key=api_, )
        return client

    def get_insights(self, question, payload_prompt, dash_out):
        prompt = f"""

        You are a skilled business data analyst.

        Your task is to generate clear, detailed, and easy-to-understand insights based on comparative sales data between two time periods. The goal is to help non-technical stakeholders quickly understand performance trends, issues, or wins.

        You will receive three parts of input:

        ---

        **1. User Question:**  
        This is what the user asked in plain language.  
        "{question}"

        ---

        **2. Parsed Payload (Structured Query):**  
        This is the system-generated breakdown of the users intent and parameters used to query the data.  
        ```json
        {payload_prompt}

        ---

        **3. Output
        This is the resulting data from the query. It includes sales amounts per month across different time periods.
        {dash_out}


        Your task:
        Analyze the output and generate natural-language insights that are:
        Written in clear, easy-to-understand English.
        Suitable for business or non-technical users.
        Highlight key trends: growths, drops, monthly variations.
        Mention months that performed significantly better or worse.
        Include overall comparisons (e.g., "this year performed better than last").
        Provide a professional yet conversational summary in 1 3 short paragraphs.
        Do not repeat or restate the users question in the output.
        Make sure to consider and reflect the time periods and context described in both the User Question and Parsed Payload.
        Always provide clear reasoning for changes or patterns growth you observe. (Most Important)
        Use Indian numbering system (e.g., lakhs, crores) for all numerical values and explanations. Avoid Western format like millions or billions.
        Avoid using any special characters or formatting in your response.


        Tone: Friendly, clear, and professional. Avoid technical jargon.

        """
        # print("\nPrompt",prompt,"\n")
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]

        api_client_ = self._get_api_key_client()

        response = "".join(chunk.text for chunk in api_client_.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=self.generate_content_config,
        ))

        return response

    def conversation_bi(self, payload_data, client_id, domain_id, today, attrs_columns, prompt_template):

        query = payload_data["query"]

        # today_ = datetime.today().date()
        today_ = today

        question = query

        prompt = f"""
        You are a natural language date-query parser. Based on a user query, return a JSON with:

        1. "comparison":  
        true if query contains: vs, versus, compared to, against, with; else false.

        2. "operation":  
        If query contains:
        - "average", "avg", "mean" ? "average"
        - "count" ? "count"
        - "sum", "total", "aggregate" ? "sum"
        Else default: "sum"

        3. "metric":  
        Match first keyword (case-insensitive) or fuzzy match from these canonical options:
        - "volume" ? match "qty", "quantity", "units"
        - "amount" ? match "sales", "amount", "value", "price", "rev", "earnings", "income"
        - "margin" ? match "margin", "markup"
        Default: "amount"

        4. "attributes":  
        Fields: {attrs_columns} 
        - If a field is mentioned in the query:
            - If specific values are present (e.g., "brand amul, brittania and parle"), extract as array: "brand": ["amul","brittania", "parle"]
            - If no specific values or query uses "all", return empty array: "brand": []
        - If a field is not mentioned, do not include it in the attributes object.
        - Use fuzzy matching to correct minor spelling mistakes in field names or values. 
        - If the query contains time granularity keywords like: 
            - "by month", "monthly", "per month", "each month", include: "month": [] in the attributes object.
            - "by week", "weekly", "per week", "each week", "dow", "day of week" ? include: "dow": [] in the attributes object.
            - "by day", "by date", "daily", "per day", "each day", "on each date" ? include: "date": [] in the attributes object.

        5. "periods":  
        Extract and resolve all date periods using todays date: {today_}  
        Return each as:
        {{
          "label": "<period>",
          "start_date": "YYYY-MM-DD",
          "end_date": "YYYY-MM-DD"
        }}
        Default: "last 9 months"

        Rules:
        - Use fuzzy matching for misspelled fields or values
        - Return only valid JSON (no explanation)
        - Dates in "YYYY-MM-DD" format
        - Set "comparison": false if only one period found

        Question: {question}
        """

        print(prompt)

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]

        api_client_ = self._get_api_key_client()

        response = "".join(chunk.text for chunk in api_client_.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=self.generate_content_config,
        ))

        return response

    def conversation_bi_0_1(self, payload_data, client_id, domain_id):

        data_df_ = self.util.read_paraquet(client_id, [], ["client_id", "date"], file_type='sales')
        rundate, runday, runmonth, runyear = self.util.fetch_rundate(data_df_)

        df = pq.read_schema(self.output_path + f'/{client_id}_{"sales"}.paraquet')
        column_names = df.names
        std_cols = ['month', 'month_no', 'dow', 'day', 'year', 'dow_no', 'week_no', 'hour', 'minute', 'second', 'date',
                    'time', 'client_id', 'client_name', 'domain_id', 'domain_name', 'branch_id', 'product_id',
                    'salesman_id', 'sale_rate', 'volume', 'amount', 'purchase_price', 'total_purchase_price',
                    'other_payment', 'cash_payment',
                    '__index_level_0__']
        attrs_columns = [col for col in column_names if col not in std_cols]

        today_ = datetime.today().date()

        today = min(rundate, today_)
        # print(today)
        question_query = payload_data["query"]

        s00 = time.time()

        s0 = time.time()
        llm_context_out = self.conversation_bi(payload_data, client_id, domain_id, today, attrs_columns,
                                               prompt_template='dates')  #### First prompt hit
        e0 = time.time()
        # print(llm_context_out,"Time Take",e0-s0)
        start1 = llm_context_out.index("json")
        end = llm_context_out.rindex("```")
        str_data = llm_context_out[start1 + 4:end]
        # dict_data = ast.literal_eval(str_data)
        dict_data = json.loads(str_data)
        print(dict_data)

        e00 = time.time()

        # dict_data = {**dict_data_dates,**dict_data_metric}
        # dict_data["attributes"] = dict_data_attrs
        # print(dict_data, "Time Taken",e00-s00)

        measure_col = dict_data["metric"]

        if dict_data["comparison"] == False:
            payload_updated = {**{"client_id": client_id, "domain_id": domain_id,
                                  # "saletype":payload_data["saletype"],
                                  "start_date": datetime.strptime(dict_data["periods"][0]["start_date"],
                                                                  "%Y-%m-%d").strftime("%d-%m-%Y"),
                                  "end_date": datetime.strptime(dict_data["periods"][0]["end_date"],
                                                                "%Y-%m-%d").strftime("%d-%m-%Y"),
                                  "col_list": list(dict_data.get("attributes", {}).keys())}, **dict_data["attributes"]}
            # print("PU",payload_updated)

            data_df_ = self.util.read_paraquet(client_id, [], ["client_id", "date"], file_type='sales')
            rundate, runday, runmonth, runyear = self.util.fetch_rundate(data_df_)

            payload_updated_ = {key: value for key, value in payload_updated.items() if value != []}
            filter_ls, columns_list = self.util.paraquet_filter_ls(payload_updated_, rundate, runday, runmonth, runyear)
            print(filter_ls, columns_list)

            columns_list = list(dict.fromkeys(columns_list))
            data_df = self.util.read_paraquet(client_id, filter_ls, columns_list, file_type='sales')

            # print(data_df.shape)

            measure_col_dict = {"revenue": 'amount', "sales": 'amount', "volume": 'volume'}

            try:
                measure_col = measure_col_dict[measure_col]
            except:
                measure_col = measure_col

            merged_dict = []

            if len(payload_updated["col_list"]) > 0:
                for i in payload_updated["col_list"]:
                    result_dict = self.calc.top_sales_cal(data_df, i, measure_col, top=7, bottom=0)
                    merged_dict.append(result_dict)
            else:
                result_dict = self.calc.top_sales_cal(data_df, "client_id", measure_col, top=7, bottom=0)
                title_updated = dict_data['periods'][0]['label']
                modified_data = {key.replace('client_id', title_updated): value if not isinstance(value, list) else [
                    {k.replace('client_id', title_updated): v for k, v in item.items()} for item in value] for
                                 key, value in result_dict.items()}

                for item in modified_data['Success']:
                    if title_updated in item:
                        item[title_updated] = title_updated

                if modified_data.get("Title") == "client_id":
                    modified_data["Title"] = title_updated
                if modified_data.get("X_axis") == "client_id":
                    modified_data["X_axis"] = title_updated

                # Step 2: Capitalize and clean Title
                modified_data["Title"] = re.sub(r"[^a-zA-Z0-9\s]", "", modified_data["Title"]).title()

                merged_dict.append(modified_data)

            # print(merged_dict[0])

        else:

            payload_updated = {"client_id": client_id, "domain_id": domain_id,
                               # "saletype":payload_data["saletype"],
                               "ishierarchy": True,
                               "optionsleft": {**{
                                   "start_date": datetime.strptime(dict_data["periods"][0]["start_date"], "%Y-%m-%d"),
                                   "end_date": datetime.strptime(dict_data["periods"][0]["end_date"],
                                                                 "%Y-%m-%d").strftime("%d-%m-%Y")},
                                               **dict_data["attributes"]},
                               "optionsright": {**{
                                   "start_date": datetime.strptime(dict_data["periods"][1]["start_date"], "%Y-%m-%d"),
                                   "end_date": datetime.strptime(dict_data["periods"][1]["end_date"],
                                                                 "%Y-%m-%d").strftime("%d-%m-%Y")},
                                                **dict_data["attributes"]},
                               "col_list": list(dict_data.get("attributes", {}).keys())}
            # print("PU",payload_updated)

            if len(payload_updated["col_list"]) > 0:
                # payload_updated = {key: value for key, value in payload_updated.items() if value != []}
                payload_updated.update(
                    {side: {k: v for k, v in payload_updated.get(side, {}).items() if v != []} for side in
                     ['optionsleft', 'optionsright']})

                merged_dict = []
                result_dict_ = self.dash_obj.benchmark_2_2(payload_updated, client_id, domain_id, measure_col)
                result_dict = json.loads(result_dict_)
                # print(result_dict)
                #                result_dict[next(iter(result_dict))]['Success'] = [
                #                                                                      {k: v for k, v in item.items() if k != "type"}
                #                                                                      for item in (
                #                                                                          result_dict[next(iter(result_dict))]['Success']['optionsLeft'] +
                #                                                                          result_dict[next(iter(result_dict))]['Success']['optionsRight']
                #                                                                      )
                #                                                                  ]

                key = next(iter(result_dict))  # Get the dynamic top-level key

                left_suffix = dict_data['periods'][0]['label']
                right_suffix = dict_data['periods'][1]['label']

                label_key = result_dict[key]['X_axis']  # e.g., 'dow', 'brand'

                for item in result_dict[key]['Success']['optionsLeft']:
                    item[label_key] = f"{item[label_key].lower()}_{left_suffix}"

                for item in result_dict[key]['Success']['optionsRight']:
                    item[label_key] = f"{item[label_key].lower()}_{right_suffix}"

                # Merge and clean the Success data
                merged_success = [
                    {k: v for k, v in item.items() if k != 'type'}
                    for item in result_dict[key]['Success']['optionsLeft'] + result_dict[key]['Success']['optionsRight']
                ]

                # Build the final dictionary
                final = {
                    'Title': result_dict[key]['Title'],
                    'X_axis': result_dict[key]['X_axis'],
                    'Y_axis': result_dict[key]['Y_axis'],
                    'Success': merged_success
                }

                merged_dict.append(final)

            else:
                payload_updated["col_list"] = ["client_id"]

                merged_dict = []
                result_dict_ = self.dash_obj.benchmark_2_2(payload_updated, client_id, domain_id, measure_col)
                result_dict = json.loads(result_dict_)
                print(result_dict)

                key = next(iter(result_dict))  # Get the dynamic top-level key

                # Merge and clean the Success data
                merged_success = [
                    {k: v for k, v in item.items() if k != 'type'}
                    for item in result_dict[key]['Success']['optionsLeft'] + result_dict[key]['Success']['optionsRight']
                ]

                # Build the final dictionary
                final = {
                    'Title': result_dict[key]['Title'],
                    'X_axis': result_dict[key]['X_axis'],
                    'Y_axis': result_dict[key]['Y_axis'],
                    'Success': merged_success
                }

                title_updated = dict_data['periods'][0]['label'] + dict_data['periods'][1]['label']
                modified_data = {key.replace('client_id', title_updated): value if not isinstance(value, list) else [
                    {k.replace('client_id', title_updated): v for k, v in item.items()} for item in value] for
                                 key, value in final.items()}

                new_values = [dict_data['periods'][0]['label'], dict_data['periods'][1]['label']]
                for i, item in enumerate(modified_data['Success']):
                    if title_updated in item and i < len(new_values):
                        item[title_updated] = new_values[i]

                merged_dict.append(modified_data)

        #        s0 = time.time()
        #        llm_insights = self.get_insights(question_query, dict_data,merged_dict[0])  #### Second prompt hit - insights
        #        e0 = time.time()
        #        #print(llm_insights,"Time Take",e0-s0)
        #        merged_dict[0]['insights'] = llm_insights

        merged_dict[0]['query_context'] = dict_data

        return merged_dict[0]

    def analyze_insights(self, payload_data, client_id, domain_id):
        question = payload_data["query"]
        dict_data = payload_data["data_context"]["query_context"]

        payload_data.pop("query")
        payload_data["data_context"].pop("query_context")

        s0 = time.time()
        llm_insights = self.get_insights(question, dict_data, payload_data)  #### Second prompt hit - insights
        e0 = time.time()
        # print(llm_insights,"Time Take",e0-s0)
        merged_dict = {"insights": llm_insights}

        return llm_insights

    def get_insights_drilldown(self, payload_prompt, dash_out):

        prompt = f"""

        You are a skilled business data analyst.

        Your task is to generate clear, detailed, and easy-to-understand insights based on comparative sales data between two time periods. The goal is to help non-technical stakeholders quickly understand performance trends, issues, or wins.

        You will receive three parts of input:

        ---

        **1. User Question:**  
        This is what the user asked in plain language.  
        "{question}"

        ---

        **2. Parsed Payload (Structured Query):**  
        This is the system-generated breakdown of the users intent and parameters used to query the data.  
        ```json
        {payload_prompt}

        ---

        **3. Output
        This is the resulting data from the query. It includes sales amounts per month across different time periods.
        {dash_out}


        Your task:
        Analyze the output and generate natural-language insights that are:
        Written in clear, easy-to-understand English.
        Suitable for business or non-technical users.
        Highlight key trends: growths, drops, monthly variations.
        Mention months that performed significantly better or worse.
        Include overall comparisons (e.g., "this year performed better than last").
        Provide a professional yet conversational summary in 1 3 short paragraphs.
        Do not repeat or restate the users question in the output.
        Make sure to consider and reflect the time periods and context described in both the User Question and Parsed Payload.
        Always provide clear reasoning for changes or patterns growth you observe. (Most Important)
        Use Indian numbering system (e.g., lakhs, crores) for all numerical values and explanations. Avoid Western format like millions or billions.
        Avoid using any special characters or formatting in your response.


        Tone: Friendly, clear, and professional. Avoid technical jargon.

        """
        # print("\nPrompt",prompt,"\n")
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]

        api_client_ = self._get_api_key_client()

        response = "".join(chunk.text for chunk in api_client_.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=self.generate_content_config,
        ))

        return response

    def analyze_drilldown_insights(self,payload_data):
        request_payload = payload_data['request']
        response_body = payload_data.copy()
        response_body.pop('request')

        print(response_body)
        return 1

    # - Return ** only the SQL query **, nothing else.
    def get_sql_query(self,question,columns,user_history):
        prompt = f"""
                You are an expert in DuckDB and SQL.
                Your task is to generate a **valid DuckDB query** and return output in a strict JSON dictionary format.

                ### Rules:
                - Only use the provided column names.
                - Assume the table name is `parquet_data`.
                - Always return output in this exact dictionary format:
                {{
                  "preface": "<Write 2–3 short, natural lines that clearly explain what the user’s question means — not by repeating it, but by paraphrasing and interpreting it naturally. 
                    Focus on conveying intent, e.g., whether the user is asking for totals, comparisons, trends, or insights. 
                    Avoid robotic phrasing or generic lines like 'This overview highlights the main findings related to your question.' 
                    
                    Vary tone across these styles:
                    - If the question is analytical → 'You’re looking to analyze {{main topic}} to uncover key patterns and insights.'
                    - If it’s factual → 'You’re trying to find the total {{metric}} for {{subject}} to understand its overall value.'
                    - If it’s comparative → 'You want to compare {{subject}} against others based on {{metric}} to see which performs best.'
                    - If it’s exploratory → 'You’re exploring {{topic}} to get a quick sense of its overall contribution or performance.'
                    - If it’s time-based → 'You’re examining how {{metric}} for {{subject}} changes over time to identify trends or shifts.'
                    - If it’s a general query → 'You’re looking to understand {{topic}} from a broader perspective, focusing on key outcomes.'
                    
                    Tone should be conversational, confident, and explanatory — as if summarizing the user’s intent before showing results.
                    Do not mention SQL, DuckDB, or databases in this section.",
                  "Title": "<short descriptive title for visualization>",
                  "X-axis": ""<column to be used for x-axis, or key field>",
                  "Y-axis": "<column to be used for y-axis, or metric>",
                  "Legend": "<optional column name for legend or series distinction — e.g., category, region, or type (omit if not applicable)>",
                  "sql_query": "<valid SQL query ending with a semicolon>",
                  "Possible_charts": ["bar", "line", "pie", "table", "kpi card","histogram", "heatmap", "radar", "scatter", "donut", "treemap", "funnel", "bubble", "waterfall",etc], 
                  "col_list": ["<all columns used in the query>"]  -- include every column referenced anywhere in the query
                }}

                - The "preface" should be written in a conversational, confident tone (like ChatGPT’s natural opening sentences).  
                - It should clearly reflect the user’s question context (metric, brand, time period, etc.).  
                - Do **not** mention SQL, DuckDB, or databases in the preface.  
                - Keep it short (2–3 lines max).  

                - Do NOT add ```json or ``` at the beginning or end.
                - Always end the SQL query with a semicolon.
                - Numeric Aggregations Rule: 
                  - Always use `round()` for numeric metrics to **2 decimal places**.  
                  - For probabilities, averages, or any calculation that could be less than 1, **cast numeric values to float/double** inside the calculation to avoid integer truncation.  
                  - Example for probability of sale:  
                    round(avg(case when sale = 'yes' then 1.0 else 0.0 end), 2) as sale_rate  
                    - This ensures results like 0.25 are returned as 0.25 instead of 0.
                - Use only lowercase for:
                    - SQL keywords
                    - column names
                    - table names
                    - string literal values (e.g., 'pooja ninore' instead of 'POOJA NINORE').
                - For all string comparisons in WHERE clauses, always use lower(column_name) = 'value' to enforce case-insensitive matching.
                - Even if the query best fits a table or KPI card, still provide values for Title, X-axis, and Y-axis.
                - Choose appropriate charts based on the type of aggregation or query:
                  - Aggregated/grouped queries → ["bar", "line", "pie", "table","histogram", "heatmap", "radar", "scatter", "donut", "treemap", "funnel", "bubble", "waterfall",etc]
                  - Single numeric values (e.g., COUNT, SUM, AVG) → ["kpi card", "table"]
                  - Non-aggregated / listing queries → ["table"]

                ### Process:
                1. **Review the User’s Question**: Start by reviewing the **User Question** to understand what the user is asking.
                2. **Check the User History**: Look at the provided `{user_history}` dictionary. If the user has asked similar questions in the past, check if any **columns, filters, or groupings** used in the past query can be applied to the current question.
                3. **Adapt the Query**: Adjust the new query based on the context from **previous questions**. This includes:
                   - **Referencing columns** or **metrics** used in past queries.
                   - **Applying relevant filters** (e.g., a department filter if it was used in previous queries).
                   - **Handling new aggregations** or computations based on prior patterns.
                4. **Generate the SQL**: Based on the context from step 3, generate a new SQL query, ensuring it is consistent and adheres to the rules of formatting and aggregation.
                5. **Validate the Query**: Ensure the SQL query is valid and logically consistent. If any inconsistencies or errors are found, adjust the query accordingly.
                6. **Output the Query**: Return the final query in the strict JSON format, including all necessary fields like Title, X-axis, Y-axis, and column references.

                ### Example:
                User Question: {question}
                Columns: {columns}
                Output:
                """

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]

        api_client_ = self._get_api_key_client()

        response = "".join(chunk.text for chunk in api_client_.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=self.generate_content_config,
        ))
        response = response.replace("```json", "").replace("```", "").strip()
        if response.lower().startswith("json"):
            response = response[4:].strip()
        response_dict = json.loads(response)
        return response_dict

    # "X-axis": "<column to be used for x-axis, or key field>",
    # "X-axis": "<for single field, use the column name; for multiple fields, show a readable combined label (e.g., 'Year-Region' instead of concat(year, '-', region))>",

    def get_datatype(self,column_dict):
        prompt = f"""
        I have a Python dictionary of columns and their data types like this:

        {column_dict}

        Some of the datatypes may be incorrect. Please re-check each column and assign the most appropriate normalized datatype.  

        ### Rules for correction:
        1. The allowed normalized datatypes are only: float, integer, string, date.
        2. If a column name contains "date", "dob", "time", or "timestamp" → map to "date".
        3. If a column name contains "id", "code", "lead", or "number" → keep it as "integer" (unless it contains decimals, then use "float").
        4. If a column name contains "amount", "amt", "pay", "rate", "length", "sec", "deposit", "loan" → use "float".
        5. If a column is clearly free text (like name, address, email, comments, title, state, city, description, gender, occupation) → use "string".
        6. Otherwise, keep the given datatype if it already matches float/integer/string/date.

        Return the result strictly as a valid Python dictionary with column names as keys and the corrected datatype as values.   
        Do not include any explanation, and do not wrap the output in triple backticks.
        """
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]

        api_client_ = self._get_api_key_client()

        response = "".join(chunk.text for chunk in api_client_.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=self.generate_content_config,
        ))

        return response

    def get_query_insights(self, query_response):
        query = query_response['sql_query']
        output = query_response['success']
        question = query_response['question']
        prompt = f"""
                You are a skilled business data analyst.

                Your role is to act like a human analyst who interprets comparative sales data and explains it in simple, professional, and conversational English.

                You will receive three inputs:

                ---

                1. User Question:
                "{question}"

                ---

                2. Parsed Payload (Structured Query):
                {query}
                3.Output:
                {output}
                
                ---

                Your task:

                    -If the output contains multiple values across time periods or categories:
                        -Analyze and write natural-language insights that are:

                        -Clear, concise, and suitable for non-technical business users.

                        -Conversational and engaging, like a consultant explaining trends.

                        -Focused on growth, decline, month-to-month variations, and standout months.

                        -Including overall comparisons (e.g., "sales this year outperformed last year by X").

                        -Written in **1–3 short paragraphs** worth of content but formatted strictly as **bullet points only**.

                        -Always provide reasoning for changes or patterns observed.

                        -Use **Indian numbering system (lakhs, crores)** for numbers.

                        -Present the final insights in bullet points, not paragraphs.
                        
                        -**Do not start with any introductory sentence or heading.** 
                            Begin directly with bullet points.

                    -If the output contains only a single aggregate value (like sum, average, max, min):

                        -State the result clearly and professionally.

                        -Keep it short and to the point, in **one or two bullet points only**.

                        -Do not add forced business interpretations or irrelevant stories.
                        -**Do not include any introductory text or heading — start directly with bullet points.**
                        
                Tone:
                Friendly, clear, professional, and human — like ChatGPT giving smart but simple business insights.
                """
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        api_client_ = self._get_api_key_client()

        response = "".join(chunk.text for chunk in api_client_.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=self.generate_content_config,
        ))
        return response

    def get_sql_query_1(self, question, columns):
        prompt = f"""
                You are an expert in DuckDB and SQL.
                Your task is to generate a **valid DuckDB query** and return output in a strict JSON dictionary format.

                ### Rules:
                - Only use the provided column names.
                - Assume the table name is `parquet_data`.
                - Always return output in this exact dictionary format:
                {{
                  "preface": "<Write 2–3 short, natural lines that clearly explain what the user’s question means — not by repeating it, but by paraphrasing and interpreting it naturally. 
                    Focus on conveying intent, e.g., whether the user is asking for totals, comparisons, trends, or insights. 
                    Avoid robotic phrasing or generic lines like 'This overview highlights the main findings related to your question.' 

                    Vary tone across these styles:
                    - If the question is analytical → 'You’re looking to analyze {{main topic}} to uncover key patterns and insights.'
                    - If it’s factual → 'You’re trying to find the total {{metric}} for {{subject}} to understand its overall value.'
                    - If it’s comparative → 'You want to compare {{subject}} against others based on {{metric}} to see which performs best.'
                    - If it’s exploratory → 'You’re exploring {{topic}} to get a quick sense of its overall contribution or performance.'
                    - If it’s time-based → 'You’re examining how {{metric}} for {{subject}} changes over time to identify trends or shifts.'
                    - If it’s a general query → 'You’re looking to understand {{topic}} from a broader perspective, focusing on key outcomes.'

                    Tone should be conversational, confident, and explanatory — as if summarizing the user’s intent before showing results.
                    Do not mention SQL, DuckDB, or databases in this section.",
                  "Title": "<short descriptive title for visualization>",
                  "X-axis": ""<column to be used for x-axis, or key field>",
                  "Y-axis": "<column to be used for y-axis, or metric>",
                  "Legend": "<optional column name for legend or series distinction — e.g., category, region, or type (omit if not applicable)>",
                  "sql_query": "<valid SQL query ending with a semicolon>",
                  "Possible_charts": ["bar", "line", "pie", "table", "kpi card","histogram", "heatmap", "radar", "scatter", "donut", "treemap", "funnel", "bubble", "waterfall",etc], 
                  "col_list": ["<all columns used in the query>"]  -- include every column referenced anywhere in the query
                }}

                - The "preface" should be written in a conversational, confident tone (like ChatGPT’s natural opening sentences).  
                - It should clearly reflect the user’s question context (metric, brand, time period, etc.).  
                - Do **not** mention SQL, DuckDB, or databases in the preface.  
                - Keep it short (2–3 lines max).  

                - Do NOT add ```json or ``` at the beginning or end.
                - Always end the SQL query with a semicolon.
                - Numeric Aggregations Rule: 
                  - Always use `round()` for numeric metrics to **2 decimal places**.  
                  - For probabilities, averages, or any calculation that could be less than 1, **cast numeric values to float/double** inside the calculation to avoid integer truncation.  
                  - Example for probability of sale:  
                    round(avg(case when sale = 'yes' then 1.0 else 0.0 end), 2) as sale_rate  
                    - This ensures results like 0.25 are returned as 0.25 instead of 0.
                - Use only lowercase for:
                    - SQL keywords
                    - column names
                    - table names
                    - string literal values (e.g., 'pooja ninore' instead of 'POOJA NINORE').
                - For all string comparisons in WHERE clauses, always use lower(column_name) = 'value' to enforce case-insensitive matching.
                - Even if the query best fits a table or KPI card, still provide values for Title, X-axis, and Y-axis.
                - Choose appropriate charts based on the type of aggregation or query:
                  - Aggregated/grouped queries → ["bar", "line", "pie", "table","histogram", "heatmap", "radar", "scatter", "donut", "treemap", "funnel", "bubble", "waterfall",etc]
                  - Single numeric values (e.g., COUNT, SUM, AVG) → ["kpi card", "table"]
                  - Non-aggregated / listing queries → ["table"]

                ### Process:
                1. **Review the User’s Question**: Start by reviewing the **User Question** to understand what the user is asking.
                3. **Adapt the Query**: Adjust the new query based on the context from **previous questions**. This includes:
                   - **Referencing columns** or **metrics** used in past queries.
                   - **Applying relevant filters** (e.g., a department filter if it was used in previous queries).
                   - **Handling new aggregations** or computations based on prior patterns.
                4. **Generate the SQL**: Based on the context from step 3, generate a new SQL query, ensuring it is consistent and adheres to the rules of formatting and aggregation.
                5. **Validate the Query**: Ensure the SQL query is valid and logically consistent. If any inconsistencies or errors are found, adjust the query accordingly.
                6. **Output the Query**: Return the final query in the strict JSON format, including all necessary fields like Title, X-axis, Y-axis, and column references.

                ### Example:
                User Question: {question}
                Columns: {columns}
                Output:
                """

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]

        api_client_ = self._get_api_key_client()

        response = "".join(chunk.text for chunk in api_client_.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=self.generate_content_config,
        ))
        response = response.replace("```json", "").replace("```", "").strip()
        if response.lower().startswith("json"):
            response = response[4:].strip()
        response_dict = json.loads(response)
        return response_dict


if __name__ == "__main__":
    a = AnalyticalFilter()
    question='give number of user working in marketing between age of 30-50 and having remark Good'
    columns=['id','name','age','join_date','active','salary','rating','department','email','remarks']
    z1 = a.get_sql_query(question,columns)
    print(z1)





