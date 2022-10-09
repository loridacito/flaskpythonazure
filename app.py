#!/usr/bin/python3
import json
import os
import pymysql
from flask import Flask, Response, request, redirect, url_for, send_from_directory
app = Flask(__name__)
# Database connection parameters - update as needed

DB_USER=os.getenv('DB_USER') or 'pythontest@mysqlforlamp'
DB_PSWD=os.getenv('DB_PSWD') or 'av19&rBB7$Uwf'
DB_NAME=os.getenv('DB_NAME') or 'task_logger'
DB_HOST=os.getenv('DB_HOST') or 'mysqlforlamp.mysql.database.azure.com'



db = pymysql.connect(host=DB_HOST, 
										 user=DB_USER, 
										 password=DB_PSWD, 
										 database=DB_NAME, 
										 cursorclass=pymysql.cursors.DictCursor)
cursor = db.cursor()

# Create a new task
@app.route('/', methods=['POST'])
def create_task():
	try:
		param = list(request.args.to_dict().keys())
		title = None
		if param != []:
			title = get_task_title(param[0])
		if not title_is_valid(title):
			resp = ''
			status = 400
		else:
			cursor.execute("INSERT INTO tasks (title) VALUES (%s)", title)
			db.commit()
			cursor.execute("SELECT MAX(id) AS id FROM tasks")
			row = cursor.fetchone()
			resp = get_task(row['id'])[0]
			status = 201
	except Exception as e:
		resp = str(e)
		status = 500
	r = Response(response=json.dumps(resp), status=status, mimetype="application/json")
	r.headers["Content-Type"] = "application/json; charset=utf-8"
	r.headers["Status"] = "Status: %d %s" % (status, get_status_msg(status));
	return r

# Get all tasks
@app.route('/', methods=['GET'])

def get_tasks():
	param = list(request.args.to_dict().keys())
	id = None
	if param != []:
		id = get_task_id(param[0])

	try:
		if id is None:
			cursor.execute("SELECT id, title, date_format(created, '%Y-%m-%d %H:%i') as created FROM tasks")
			resp = cursor.fetchall()
			status = 200
		else:
			id = param[0]
			cursor.execute("SELECT id, title, date_format(created, '%Y-%m-%d %H:%i') as created \
										FROM tasks WHERE id="+str(id))
			row = cursor.fetchone()
			if row is not None:
				resp = row	
				status = 200
			else:
				resp = ''
				status = 404

	except Exception as e:
		resp = str(e)
		status = 500
	r = Response(response=json.dumps(resp), status=status, mimetype="application/json")
	r.headers["Content-Type"] = "application/json; charset=utf-8"
	r.headers["Status"] = "Status: %d %s" % (status, get_status_msg(status));
	return r	

# Get an individual task
def get_task(id):
	try:
		cursor.execute("SELECT id, title, date_format(created, '%Y-%m-%d %H:%i') as created \
										FROM tasks WHERE id="+str(id))
		row = cursor.fetchone()
		return (row if row is not None else '', 200 if row is not None else 404)
	except Exception as e:
		return ('', 404)

		
# Update an existing task
@app.route('/', methods=['PUT'])
def update_task():
	param = list(request.args.to_dict().keys())
	title = None
	id = None
	if param != []:
		title = get_task_title(param[0])
		id = get_task_id(param[0])
	try:
		if not title_is_valid(title):
			resp = ''
			status = 400
		else:
			cursor.execute("UPDATE tasks SET title=%s WHERE id=%s", (title, id))
			db.commit()
			respon = get_task(id)
			resp = respon[0]
			status = respon[1]
	except Exception as e:
		resp = str(e)
		status = 500
	r = Response(response=json.dumps(resp), status=status, mimetype="application/json")
	r.headers["Content-Type"] = "application/json; charset=utf-8"
	r.headers["Status"] = "Status: %d %s" % (status, get_status_msg(status));
	return r
		
# Delete an existing task
@app.route('/', methods=['DELETE'])
def delete_task():
	try: 
		param = list(request.args.to_dict().keys())
		id = None
		if param != []:
			id = get_task_id(param[0])
		respon = get_task(id)
		if respon[1] == 200:
			cursor.execute("DELETE FROM tasks WHERE id=%s", id)
			db.commit()
			resp = ''
			status = 200
		else:
			resp = respon[0]
			status = respon[1]
	except Exception as e:
		resp = str(e)
		status = 500
	r = Response(response=json.dumps(resp), status=status, mimetype="application/json")
	r.headers["Content-Type"] = "application/json; charset=utf-8"
	r.headers["Status"] = "Status: %d %s" % (status, get_status_msg(status));
	return r	

# Returns the HTTP request method
def get_method():
	return os.getenv('REQUEST_METHOD') or 'GET'

# Returns the query string	
#def get_query_string():
#	query_string = os.getenv('QUERY_STRING') or ''
#	return query_string.replace('%20', ' ').replace('%2F', '/').replace('+', ' ')

# Returns the task ID if set in the request query string
def get_task_id(query_string):
#	query_string = get_query_string()
	qs_parts = query_string.split('/')
	return qs_parts[0] if qs_parts[0].isnumeric() else None

# Returns the task title from the query string if set
def get_task_title(query_string):
	title = None
#	query_string = get_query_string()
	if query_string != '':
		qs_parts = query_string.split('/')
		title = qs_parts[1] if len(qs_parts) > 1 else qs_parts[0]
		title = None if title.isnumeric() else title
	return title

# Returns True if title is valid, False otherwise
def title_is_valid(title):
	return True if isinstance(title, str) and len(title) >= 6 and len(title) <= 255 else False
	
# Returns a status code method
def get_status_msg(code):
	msg = 'OK'
	msg = 'Created' if code == 201 else msg
	msg = 'Not Found' if code == 404 else msg
	msg = 'Bad Request' if code == 400 else msg
	msg = 'Internal Server Error' if code == 500 else msg
	return msg

method = get_method()
#id = get_task_id()
#title = get_task_title()
'''
if method == 'GET' and not id is None:
	resp = get_task(id)
elif method == 'GET':
	resp = get_tasks()
elif method == 'DELETE':
	resp = delete_task(id)
elif not title_is_valid(title):
	resp = ('', 400)
elif method == 'POST':
	resp = create_task(title)
elif method == 'PUT':
	resp = update_task(id, title)

#print("Status: %d %s" % (resp[1], get_status_msg(resp[1])))
#print("Content-type: application/json\n")
#print(json.dumps(resp[0]))
'''
if __name__ == '__main__':
   app.run()