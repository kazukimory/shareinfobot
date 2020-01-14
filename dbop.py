import os

import sqlite3

dbname = 'info.db'

conn = sqlite3.connect(dbname)
c = conn.cursor()

sql = 'insert into userinfo (id, name, height, weight, dateofbirth, personality) values (?,?,?,?,?,?)'
info = (1, "michael", 164, 70, "1998年5月6日", "二重国籍")
conn.execute(sql, info)

conn.commit()

select_sql = 'select * from userinfo'

c.execute(select_sql)
result = c.fetchone()

conn.close()

print(result)
