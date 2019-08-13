import psycopg2.pool


class DBConnection:
    def __init__(self, prod_connection_string):
        self.conn = psycopg2.connect(
            prod_connection_string,
            sslmode='require')
        self.cursor = self.conn.cursor()

    def get_all_responses(self, query):
        try:
            self.cursor.execute(query)
            response = self.cursor.fetchall()
            return response
        except:
            return None

    def close_connection(self):
        self.conn.close()
