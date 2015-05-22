import time, sqlite3, os
from dateutil import parser
from flask import Flask, request, jsonify, url_for
from flask.ext import excel
from werkzeug import secure_filename
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
# todaysDate = time.strftime("%Y-%m-%d")
# for x in range(0,11):
#   if x<9:
#     dateVal = '0'+str(x+1)
#   else:
#     dateVal = str(x+1)
#   c.execute('''INSERT OR IGNORE INTO weights VALUES(?, ?, ?)''',(('2015-05-'+ dateVal),todaysDate,200.0))

# # Delete all rows
#c.execute('''DELETE from weights''')

db.commit()

# Render index page
@app.route('/')
def index():
  c.execute('''SELECT weight FROM weights ORDER BY date desc limit 1''')
  print('before fetchall')
  latestweight = c.fetchall()
  if not latestweight:
    latestweight.append(0)
    print 'list empty'
    print latestweight
  print(latestweight[0])
  print('Send index to template')
  # Return the most recent weight, and todays date to preload the add weight form
  return template.render(currentdate=time.strftime("%Y-%m-%d"),
    latestweight = latestweight[0],
    url_for=url_for)

# Process a file upload
@app.route("/upload", methods=['GET', 'POST'])
def upload_file():
  if request.method == 'POST':
    todaysDate = time.strftime("%Y-%m-%d")
    loadedData = request.get_array(field_name='file')
    # Test for header row
    # TODO: test this code, make sure it works
    if loadedData[0][0].isdigit():
      print "no header to delete"
    else:
      print "deleted a header row"
      del loadedData[0]

    for row in loadedData:
      # TODO: Add an error check for the parsed date
      row[0] = parser.parse(row[0]).date()
      if row[1]:
        c.execute('''UPDATE OR IGNORE weights SET date=?, dateSubmitted=?, weight=? WHERE date=?''',(row[0], todaysDate, row[1], row[0]))
        c.execute('''INSERT OR IGNORE INTO weights (date,dateSubmitted,weight) VALUES (?, ?, ?)''',(row[0], todaysDate, row[1]))
    db.commit()
    print 'excel file data loaded'
    # TODO: Figure out how to pass the updated table back to automatically refresh?
    return jsonify({"result": request.get_array(field_name='file')})
  return '''
  <!doctype html>
  <title>Upload an excel file</title>
  <h1>Excel file upload (csv, tsv, csvz, tsvz only)</h1>
  <form action="" method=post enctype=multipart/form-data><p>
  <input type=file name=file><input type=submit value=Upload>
  </form>
  '''
# Process a file download
# TODO: Implement file download
@app.route("/download", methods=['GET'])
def download_file():
    return excel.make_response_from_array([[1,2], [3, 4]], "csv")

# Process weight row functions
@app.route('/weights', methods=['POST','GET'])
def weights():
  error = None
  todaysDate = time.strftime("%Y-%m-%d")
  if request.method == 'POST':
    if 'deleterow' in request.form:
      # Delete the row in the database
      c.execute('''DELETE FROM weights WHERE rowid=?''',(request.form['deleterow'],))
      db.commit()
      print 'Row deleted in the table'
      returnValue = jsonify(result=request.form['deleterow'])

    elif 'editrow' in request.form:
      # Edit the row in the database
      c.execute('''UPDATE weights SET rowid=?, date=?, dateSubmitted=?, weight=? WHERE rowid=?''',(
          request.form['editrow'],
          request.form['date'],
          todaysDate,
          request.form['weight'],
          request.form['editrow']))
      db.commit()
      print 'Row edited in the table'
      returnValue = jsonify(result=(
          request.form['editrow'],
          request.form['date'],
          todaysDate,
          request.form['weight']))

    elif 'addrow' in request.form:
      print request.form
      print todaysDate
      # Try to update a weight data row if the data already exists, and if it doesn't exist, insert it
      c.execute('''UPDATE OR IGNORE weights SET date=?, dateSubmitted=?, weight=? WHERE date=?''',(
          request.form['date'],
          todaysDate,
          request.form['weight'],
          request.form['date']))
      c.execute('''INSERT OR IGNORE INTO weights (date,dateSubmitted,weight) VALUES (?, ?, ?)''',(
          request.form['date'],
          todaysDate,
          request.form['weight']))
      db.commit()
      c.execute('''SELECT rowid,* FROM weights WHERE date=?''',(request.form['date'],))
      fetchEditedRow = c.fetchall() # TODO: Should this be fetchone()?
      print 'Row added or updated on the table'
      returnValue = jsonify(result=fetchEditedRow[0])
      print fetchEditedRow
    else:
      # TODO: log an error?
      pass
  else:
    returnValue = retrieveWeighttable()
  return returnValue

def retrieveWeighttable():
  # Fetch the inital table to put into DataTables and the chart
  c.execute('''SELECT rowid,* FROM weights''')
  weights = c.fetchall()
  print 'Table retrieved'
#   print weights
  return jsonify(weights=weights)


if __name__ == '__main__':
  # app.run(debug=True, host='0.0.0.0', port=8080)
  app.run(host='0.0.0.0', port=8080)