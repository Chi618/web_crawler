import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup
import sqlalchemy as db
from flask import Flask, render_template, send_file
import matplotlib.pyplot as plt
from io import BytesIO
app = Flask(__name__)

# Database configuration
server = 'DESKTOP-74ONRIV'  # Your server name
database = 'test'            # Your database name
connection_string = f'mssql+pyodbc://{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server'
engine = db.create_engine(connection_string)

# 爬蟲部分
def scrape_stock_data():
    today_date = datetime.datetime.now()
    date_list = []
    for i in range(2):
        i_date = today_date - datetime.timedelta(days=i)
        date_list.append(i_date.strftime('%Y%m%d'))

    stock_price_data = pd.DataFrame()

    for i_date in date_list:
        url = 'https://www.twse.com.tw/exchangeReport/MI_INDEX?response=html&date=' + i_date + '&type=ALLBUT0999'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        if '很抱歉，沒有符合條件的資料!' in soup.text:
            continue

        table = soup.find_all('table')[8]
        column_names = table.find('thead').find_all('tr')[2].find_all('td')
        column_names = [elem.getText() for elem in column_names]
        row_datas = table.find('tbody').find_all('tr')
        rows = []
        for row in row_datas:
            rows.append([elem.getText().replace(',', '').replace('--', '') for elem in row.find_all('td')])
        df = pd.DataFrame(data=rows, columns=column_names)

        df.insert(0, '日期', i_date, True)
        df.insert(1, '時間', datetime.datetime.now(), True)  # Add current timestamp column

        stock_price_data = pd.concat([stock_price_data, df])

    stock_price_data.to_csv('stock_price_data.csv', index=False)

# 讀取股票資料
def load_stock_data():
    try:
        stock_price_data = pd.read_csv('stock_price_data.csv')
        if stock_price_data.empty:
            raise pd.errors.EmptyDataError
        print("已成功讀取股票資料")
    except (FileNotFoundError, pd.errors.EmptyDataError):
        # 如果檔案不存在或內容為空，執行爬蟲來獲取資料
        scrape_stock_data()
        # 再次嘗試讀取資料
        stock_price_data = pd.read_csv('stock_price_data.csv')
    return stock_price_data

# 寫入資料庫
def write_to_database(dataframe):
    try:
        # 寫入資料庫，排除第一欄
        dataframe.to_sql('stock', engine, if_exists='replace', index=False)

        print("資料已成功寫入資料庫")
    except Exception as e:
        print(f"Error: {e}")

# Route to display data
@app.route('/')
def display_data():
    try:
        # Query data from the database
        query = "SELECT * FROM stock"
        df = pd.read_sql(query, engine)

        # Convert DataFrame to HTML table
        html_table = df.to_html(index=False)

         # Include link to bar chart route
        bar_chart_link = '<a href="/bar_chart">View Bar Chart</a>'
        

        return render_template('index.html', table=html_table, bar_chart_link=bar_chart_link)
    except Exception as e:
        return f"Error: {e}"

# Route to display bar chart and pie chart
@app.route('/bar_chart')
def display_bar_and_pie_chart():
    try:
        # Query data from the database
        query = "SELECT * FROM stock"
        df = pd.read_sql(query, engine)

        # Count the values in the "漲跌(+/-)" column
        value_counts = df['漲跌(+/-)'].value_counts()

        # Plot the bar chart
        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)  # Subplot for bar chart
        value_counts.plot(kind='bar', color='skyblue')
        plt.title('Count of Up or Down(+/-)')
        plt.xlabel('Up or Down(+/-)')
        plt.ylabel('Count')
        plt.xticks(rotation=0)

        # Plot the pie chart
        plt.subplot(1, 2, 2)  # Subplot for pie chart
        plt.pie(value_counts, labels=value_counts.index, autopct='%1.1f%%', startangle=140)
        plt.title('Percentage of Up or Down(+/-)')
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle

        plt.tight_layout()  # Adjust layout to prevent overlap

        # Save the combined plot to a bytes buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)

        plt.close()  # Close the plot to release memory

        return send_file(buffer, mimetype='image/png')
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    # 執行爬蟲
    scrape_stock_data()

    # 讀取資料
    stock_price_data = load_stock_data()

    # 寫入資料庫
    write_to_database(stock_price_data)

    # Run Flask app
    app.run(debug=True)
