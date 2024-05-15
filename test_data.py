import pyodbc
import csv

# 設定資料庫連接資訊
server = 'DESKTOP-74ONRIV'  # 你的伺服器名稱
database = 'test'            # 你的資料庫名稱

# 使用Windows驗證
connection_string = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server + ';DATABASE=' + database + ';Trusted_Connection=yes;'

try:
    # 建立資料庫連接
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    
    # 執行查詢
    cursor.execute("SELECT * FROM stock")
    
    # 取得查詢結果
    rows = cursor.fetchall()
    
    # 取得欄位名稱
    columns = [column[0] for column in cursor.description]
    
    # 將資料寫入CSV檔案
    with open('stock_data_假資料.csv', 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        
        # 寫入欄位名稱
        csvwriter.writerow(columns)
        
        # 寫入資料
        csvwriter.writerows(rows)
    
    print("資料已成功寫入stock_data_假資料.csv")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    # 關閉資料庫連接
    if 'conn' in locals():
        conn.close()
