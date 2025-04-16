from flask import Flask, render_template, request
from pymongo import MongoClient
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# MongoDB connection
client = MongoClient("mongodb+srv://yannabathularamesh:root@cluster0.idjobj1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['mess_db']
enrollments = db['enrollments']

# Home Page
@app.route('/')
@app.route('/index.html')
def home():
    return render_template('index.html')

# Enroll Page
@app.route('/enroll.html', methods=['GET', 'POST'])
def enroll():
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'phone': request.form.get('phone'),
            'days': int(request.form.get('days')),
            'startdate': request.form.get('startdate'),
            'breakfast': 'breakfast' in request.form,
            'lunch': 'lunch' in request.form,
            'dinner': 'dinner' in request.form,
            'amount': int(request.form.get('amount'))
        }
        enrollments.insert_one(data)
        return f"<h2>Thank you for enrolling, {data['name']}! Total Cost: ₹{data['amount']}</h2>"

    return render_template('enroll.html')

# Due Page
@app.route('/due.html', methods=['GET', 'POST'])
def due_page():
    dues = []
    checked = False

    if request.method == 'POST':
        checked = True
        checkdate_str = request.form.get('checkdate')
        check_date = datetime.strptime(checkdate_str, "%Y-%m-%d")

        # Fetch all enrollments
        records = enrollments.find()

        for record in records:
            try:
                start_date = datetime.strptime(record['startdate'], "%Y-%m-%d")
                total_days = int(record['days'])
                end_date = start_date + timedelta(days=total_days)

                # If selected date is before start, no dues
                if check_date < start_date:
                    continue

                # Calculate days the user owes after the end date
                if check_date > end_date:
                    extra_days = (check_date - end_date).days
                else:
                    extra_days = 0

                # Only calculate cost for extra days (not the original days)
                if extra_days > 0:
                    daily_cost = 0
                    if record.get('breakfast'): daily_cost += 20
                    if record.get('lunch'): daily_cost += 40
                    if record.get('dinner'): daily_cost += 40

                    total_due = daily_cost * extra_days

                    dues.append({
                        'name': record['name'],
                        'phone': record['phone'],
                        'startdate': record['startdate'],
                        'enddate': end_date.strftime("%Y-%m-%d"),
                        'extra_days': extra_days,
                        'meals': {
                            'breakfast': record.get('breakfast', False),
                            'lunch': record.get('lunch', False),
                            'dinner': record.get('dinner', False),
                        },
                        'due_amount': total_due
                    })
            except Exception as e:
                print("Error calculating due for record:", record)
                print("Error:", e)

    return render_template('due.html', dues=dues, checked=checked)

# List Page
@app.route('/list.html')
def list_page():
    enrollments_list = list(enrollments.find())
    for e in enrollments_list:
        try:
            start = datetime.strptime(e['startdate'], "%Y-%m-%d")
            end = start + timedelta(days=int(e['days']))
            e['enddate'] = end.strftime("%Y-%m-%d")
        except Exception as ex:
            print("Error calculating end date:", ex)
            e['enddate'] = 'Invalid'

    return render_template('list.html', enrollments=enrollments_list)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) 
    app.run(host='0.0.0.0', port=port)
