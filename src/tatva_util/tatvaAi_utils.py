import json
from google import genai
from google.genai import types

class Tatva_Utils():
    def __init__(self):
        self.api_counter = 0
        self.api_limit = 250

        ### APIS -- [Sam Navaantrix, Sam Personal]
        self.api_keys = ['AIzaSyCt5OmpfOgpRJSaa1XbacyLAQGs7IVyrDY','AIzaSyB8bDMs2rrY0sunI08b3x7bUL5qbc2qUiE','AIzaSyCaJa2tp4WXmWMNZr2WFkHqiz4RwEkla24',]  ##
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
            "making_charges",
            "making_per_gm"
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

    def get_sql_query(self, question, columns, user_history):
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