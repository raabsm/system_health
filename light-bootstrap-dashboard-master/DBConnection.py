import psycopg2.pool

prod_connection_string = "dbname='skywatch_prod' user='skywatch@skywatchdb-prod.postgres.database.azure.com' " \
                         "host='skywatchdb-prod.postgres.database.azure.com' password='SkyWatch1234'"

conn = psycopg2.connect(
    prod_connection_string,
    sslmode='require')
cursor = conn.cursor()


def get_all_responses(query):
    try:
        cursor.execute(query)
        response = cursor.fetchall()
        return response
    except:
        return None


def close_connection():
    conn.close()
