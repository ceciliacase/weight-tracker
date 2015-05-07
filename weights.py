import time
import sqlite3
from flask import Flask, request, jsonify
from jinja2 import Environment, PackageLoader, Template
env = Environment(loader=PackageLoader('weights','./'))

template = env.get_template('index.j2')

app = Flask(__name__)

db = sqlite3.connect('weights.sqlite3')
c  = db.cursor()

# Create the database if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS weights (date text, dateSubmitted text, weight real)''')
db.commit()

# Add dummy lines to the database
# c.execute('''INSERT INTO weights VALUES('2015-04-30','2015-04-30',185.6)''')

# # Delete all rows
#c.execute('''DELETE from weights''')

db.commit()

# actions = { 'delete': delete_function,
#             'add':    add_function
#             'update': update_function}


@app.route('/')
def index():
	c.execute('''SELECT rowid,* FROM weights''')
	weights = c.fetchall()
	return template.render(weights=weights)

@app.route('/weights', methods=['POST','GET'])
def weights():
	error = None
	todaysDate = time.strftime("%Y-%m-%d")
	if request.method == 'POST':
		# print request.form['weight']
		# print request.form['date']
		if 'deletethis' in request.form:
			# do delete stuffs
			rowIdToDelete = request.form['deletethis']
			print rowIdToDelete
			c.execute('''DELETE FROM weights WHERE rowid=?''',(rowIdToDelete,))
			# c.execute('''DELETE FROM weights WHERE rowid=11''')
			db.commit()
			returnValue = jsonify(result=rowIdToDelete)
		elif 'editthis' in request.form:
			# do edit stuffs
			weightdata = request.form['editthis'], request.form['date'], todaysDate,request.form['weight']
			rowIdToEdit = request.form['editthis']
			print weightdata
			print rowIdToEdit
			# Try to update the current record, then if it doesn't exist, insert it
# 			c.execute('''UPDATE weights SET (date,dateSubmitted,weight) VALUES (?, ?, ?) WHERE rowid=?''',(weightdata[1], weightdata[2], weightdata[3]),(weightdata[0]))
			c.execute('''UPDATE weights SET rowid=?, date=?, dateSubmitted=?, weight=? WHERE rowid=?''',(weightdata[0], weightdata[1], weightdata[2], weightdata[3], weightdata[0]))
			db.commit()
			print 'End of edit loop'
			returnValue = jsonify(result=weightData[0])

		else:
			# Add weight data row
			weightdata = request.form['date'],todaysDate,request.form['weight']
			# print weightdata
			c.execute('''INSERT INTO weights (date,dateSubmitted,weight) VALUES (?, ?, ?)''',(weightdata[0],weightdata[1],weightdata[2]))
			db.commit()
			c.execute('''SELECT rowid,* FROM weights ORDER BY rowid DESC LIMIT 1''')
			fetchLastRow = c.fetchall()
			returnValue = jsonify(result=fetchLastRow[0])
	else:
		error = 'Invalid'
	return returnValue






if __name__ == '__main__':
	app.run(host='0.0.0.0')