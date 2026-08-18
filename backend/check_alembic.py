import pymysql
conn = pymysql.connect(host='localhost', user='root', password='', database='wave_notebook')
cursor = conn.cursor()
cursor.execute("SELECT version_num FROM alembic_version")
print(cursor.fetchall())
conn.close()
