import time
import sqlite3
from flask import Flask, request, jsonify
from jinja2 import Environment, PackageLoader, Template
env = Environment(loader=PackageLoader('weights','./'))

template = env.get_template('index.html')

app = Flask(__name__)

db = sqlite3.connect('weights.sqlite3')
c  = db.cursor()

# Create the database if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS weights (date text unique, dateSubmitted text, weight real)''')

# Add dummy lines to the database
# TODO: Remove this code when file upload works
todaysDate = time.strftime("%Y-%m-%d")
for x in range(0,11):
	c.execute('''INSERT OR IGNORE INTO weights VALUES(?, ?, ?)''',(('2015-05-'+ str(x+1)),todaysDate,200.0))

# # Delete all rows
#c.execute('''DELETE from weights''')

db.commit()

# actions = { 'delete': delete_function,
#             'add':    add_function
#             'update': update_function}

@app.route('/')
def index():
	c.execute('''SELECT weight FROM weights ORDER BY date desc limit 1''')
	print('before fetchall')
	latestweight = c.fetchall()
	print('Send index to template')
	return template.render(currentdate=time.strftime("%Y-%m-%d"),latestweight = latestweight[0])


@app.route('/weights', methods=['POST','GET'])
def weights():
	error = None
	todaysDate = time.strftime("%Y-%m-%d")
	if request.method == 'POST':
		if 'deleterow' in request.form:
			# Delete the row in the database
			rowIdToDelete = request.form['deleterow']
			print rowIdToDelete
			c.execute('''DELETE FROM weights WHERE rowid=?''',(rowIdToDelete,))
			# c.execute('''DELETE FROM weights WHERE rowid=11''')
			db.commit()
			returnValue = jsonify(result=rowIdToDelete)
		elif 'editrow' in request.form:
			# Edit the row in the database
			weightdata = request.form['editrow'], request.form['date'], todaysDate,request.form['weight']
			rowIdToEdit = request.form['editrow']
			# Update the current record
			c.execute('''UPDATE weights SET rowid=?, date=?, dateSubmitted=?, weight=? WHERE rowid=?''',(weightdata[0], weightdata[1], weightdata[2], weightdata[3], weightdata[0]))
			db.commit()
			returnValue = jsonify(result=weightdata)

		elif 'addrow' in request.form:
			# Add weight data row, or update it if the date selected already has a match in the database
			weightdata = request.form['date'],todaysDate,request.form['weight']

			# Try to update a row if the data already esists, and if it doesn't exist, insert it
			c.execute('''UPDATE OR IGNORE weights SET date=?, dateSubmitted=?, weight=? WHERE date=?''',(weightdata[0], weightdata[1],weightdata[2],weightdata[0]))
			c.execute('''INSERT OR IGNORE INTO weights (date,dateSubmitted,weight) VALUES (?, ?, ?)''',(weightdata[0],weightdata[1],weightdata[2]))
			db.commit()
			c.execute('''SELECT rowid,* FROM weights WHERE date=?''',(weightdata[0],))

			fetchLastRow = c.fetchall()
			returnValue = jsonify(result=fetchLastRow[0])
		else:
			pass
	else:
		# Fetch the inital table to put into DataTables
		print('Fetch inital table')
		c.execute('''SELECT rowid,* FROM weights''')
		weights = c.fetchall()
		print 'Inital table fetched'
		return jsonify(weights=weights)
	return returnValue






if __name__ == '__main__':
	app.run(host='0.0.0.0', port='8080')