from flask import Flask, request, jsonify
from flask_basicauth import BasicAuth
import re
import subprocess
import psutil
import time
import hashlib
import requests
from flaskext.mysql import MySQL
from cryptography.fernet import Fernet
app = Flask(__name__)

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '12345678'
app.config['MYSQL_DATABASE_DB'] = 'test_database'
app.config['MYSQL_DATABASE_HOST'] = '203.154.83.124'

mysql = MySQL()
mysql.init_app(app)
secure_my_api = BasicAuth(app)

def line_notify(message):
    url = "https://notify-api.line.me/api/notify"

    payload = "message=%s"%message
    headers = {
        'Content-Type': "application/x-www-form-urlencoded",
        'Authorization': "Bearer Vq3RV2jpiX68wQ3gwnbwrIwnYxpHUPpFgIJeFZaP3IJ",
        'User-Agent': "PostmanRuntime/7.13.0",
        'Accept': "*/*",
        'Cache-Control': "no-cache",
        'Postman-Token': "89cbcb24-a666-4bcd-95b8-3074f963d787,e5f1999a-95e4-4a86-8219-d19daee4f5da",
        'Host': "notify-api.line.me",
        'accept-encoding': "gzip, deflate",
        'content-length': "21",
        'Connection': "keep-alive",
        'cache-control': "no-cache"
        }

    response = requests.request("POST", url, data=payload, headers=headers)

    print(response.text)

def ping_ip(hostname):
	try:
		output = subprocess.check_output(['ping', '-c', '4', '-q', hostname])
		output = output.decode('utf8')
		statistic = re.search(r'(\d+\.\d+/){3}\d+\.\d+', output).group(0)
		avg_time = re.findall(r'\d+\.\d+', statistic)[1]
		response_time = float(avg_time)
		return response_time

	except Exception as e:
		print e

@app.route('/')
@secure_my_api.required
def securedByBasicAuth():
    app.config['BASIC_AUTH_USERNAME'] = 'sdi'
    app.config['BASIC_AUTH_PASSWORD'] = 'admin'
    return "hello"

@app.route('/cpu', methods=['GET'])
def get_cpu():
    try:
        cpu_message = {}
        used_cpu = str(psutil.cpu_percent(interval=1))
        cpu_message["CPU usuage"] = used_cpu
        return jsonify(cpu_message)
    except Exception as e:
        return e

@app.route('/mem', methods=['GET'])
def get_mem():
    try:
        mem_message= {}
        used_mem = str(psutil.virtual_memory().percent)
        mem_message["Memory usuage"] = used_mem
        return jsonify(mem_message)
    except Exception as e:
        return e

@app.route('/disk', methods=['GET'])
def get_disk():
    try:
        disk_message = {}
        used_disk = str(psutil.disk_usage('/').percent)
        disk_message["Disk usuage"] = used_disk
        return jsonify(disk_message)
    except Exception as e:
        return e

@app.route('/ping', methods=['POST'])
def ping_list():
    #ip_list = { 'destination' : ['8.8.8.8','www.google.co.th', 'www.youtube.com']}
    print (request.is_json)
    ip_list = request.get_json()
    try:
        latency_data = {}
        for ip in ip_list['destination'] :
            latency = str(ping_ip(ip))
            latency_data[ip] = "%s ms"%latency
        latency_message = {}
        latency_message["result"] = latency_data

        return jsonify(latency_message)
    except Exception as e:
        return e

@app.route('/database', methods=["POST"])
def insertDB():
    name_content = request.get_json()
    username = name_content["username"]
    password = name_content["password"]

    hash_password = hashlib.sha384(b'%s'%password)
    hex_dig_password = hash_password.hexdigest()
    print hex_dig_password

    current_time = time.time()
    connect = mysql.connect()
    cursor = connect.cursor()
    try:
        sql = "INSERT INTO users (username, password, create_time) VALUE (%s, %s, %s)"  # INSERT INTO [table name]
        value = (username, hex_dig_password, current_time)
        cursor.execute(sql, value)

        connect.commit()
        connect.close()
        line_notify(str(username))
        return sql%value
    except Exception as error:
        print(error)
        connect.rollback()  # if error to insert every thing can insert is comeback
        connect.close()

def selectUser(username):
    connect = mysql.connect()
    cursor = connect.cursor() #access to edit database

    try:
        select = 'SELECT * FROM users WHERE username = %s'
        cursor.execute(select, username)
        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        result_pool = toJson(data, columns)
        print(result_pool)
        return result_pool

    except Exception as error:
        print(error)
        connect.rollback() #if error to insert every thing can insert is comeback
        connect.close()

app.run(host="0.0.0.0")
