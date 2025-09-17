from flask import Flask, request, render_template, redirect, session, url_for
from datetime import datetime, time

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

hosts_path = 'C:/Windows/System32/drivers/etc/hosts'
redirect_address = "127.0.0.1"

blocked_websites_key = 'blocked_websites'
messages_key = 'messages'

# User credentials with blocked websites and time spans
users = {
    'admin': {'password': '123', 'messages': [], 'blocked_websites': {}},
}

def block_websites_for_user(username, websites, start_time, end_time):
    user = users.get(username)
    if user:
        user['blocked_websites'] = user.get('blocked_websites', {})
        if 'websites' not in user['blocked_websites']:
            user['blocked_websites']['websites'] = []
        user['blocked_websites']['websites'].extend(websites)
        user['blocked_websites']['start_time'] = start_time
        user['blocked_websites']['end_time'] = end_time
        # Write websites to the host file
        with open(hosts_path, "a") as file:
            for site in websites:
                file.write(redirect_address + " " + site + "\n")
        return f"Websites successfully blocked for {username} from {start_time} to {end_time}."
    return f"User '{username}' not found."


# Block for all users
def block_websites_for_all_users(websites, start_time, end_time):
    for username, user in users.items():
        if username != 'admin':
            user['blocked_websites'] = {
                'websites': websites,
                'start_time': start_time,
                'end_time': end_time
            }
            # Write websites to the host file for all users
            with open(hosts_path, "a") as file:
                for site in websites:
                    file.write(redirect_address + " " + site + "\n")
    return f"Websites successfully blocked for all users from {start_time} to {end_time}."

def unblock_websites_for_user(username):
    user = users.get(username)
    if user:
        blocked_websites = user.get('blocked_websites', {}).get('websites', [])
        with open(hosts_path, "r") as file:
            lines = file.readlines()
        with open(hosts_path, "w") as file:
            for line in lines:
                if not any(site in line for site in blocked_websites):
                    file.write(line)
        user['blocked_websites'] = {}
        return f"Websites successfully unblocked for {username}."
    return f"User '{username}' not found."

# unblock for all users
def unblock_websites_for_all_users():
    for username, user in users.items():
        if username != 'admin':
            user['blocked_websites'] = {}
    with open(hosts_path, "w") as file:
        file.write("")
    return f"Websites successfully unblocked for all users."

def is_website_blocked_for_user(username, website):
    user = users.get(username)
    if user:
        blocked_websites = user.get('blocked_websites', {})
        if blocked_websites:
            websites = blocked_websites.get('websites', [])
            return website in websites
    return False

def is_user_blocked_at_current_time(username):
    user = users.get(username)
    if user:
        blocked_websites = user.get('blocked_websites', {})
        if blocked_websites:
            start_time = blocked_websites.get('start_time')
            end_time = blocked_websites.get('end_time')
            current_time = datetime.now().time()
            return start_time <= current_time <= end_time
    return False

@app.route('/')
def index():
    if 'username' in session:
        if session['username'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            session['username'] = username
            if username == 'admin':
                return redirect(url_for('add_website'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html', error='')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop(blocked_websites_key, None)
    return redirect(url_for('login'))

@app.route('/add_website', methods=['GET', 'POST'])
def add_website():
    if 'username' in session and session['username'] == 'admin':
        if request.method == 'POST':
            username = request.form['username']
            action = request.form['action']
            websites = request.form.getlist('websites')  # Get list of websites
            start_time = datetime.strptime(request.form['start_time'], "%H:%M").time()
            end_time = datetime.strptime(request.form['end_time'], "%H:%M").time()
            if username == 'all':
                if action == 'block':
                    result = block_websites_for_all_users(websites, start_time, end_time)
                elif action == 'unblock':
                    result = unblock_websites_for_all_users()
            else:
                if action == 'block':
                    result = block_websites_for_user(username, websites, start_time, end_time)
                elif action == 'unblock':
                    result = unblock_websites_for_user(username)
            return render_template('add_website.html', success=result)
        elif request.method == 'GET':
            if 'logout' in request.args:
                return redirect(url_for('logout'))
            return render_template('add_website.html', users=users) 
    return redirect(url_for('login'))

@app.route('/user_dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if 'username' in session and session['username'] != 'admin':
        username = session['username']
        user = users.get(username)
        all_blocked_websites = []
        if user:
            blocked_websites_info = user.get('blocked_websites', {})
            if blocked_websites_info:
                websites = blocked_websites_info.get('websites', [])
                start_time = blocked_websites_info.get('start_time')
                end_time = blocked_websites_info.get('end_time')
                all_blocked_websites.extend([(website, start_time, end_time) for website in websites])
        print("All Blocked Websites for user {}: {}".format(username, all_blocked_websites)) 
        if request.method == 'POST':
            message = request.form['message']
            admin_messages = users['admin']['messages']
            sender_username = session['username']
            admin_messages.append((sender_username, message, datetime.now()))
            return redirect(url_for('user_dashboard'))
        return render_template('user_dashboard.html', username=username, blocked_websites=all_blocked_websites)
    return redirect(url_for('login'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'username' in session and session['username'] == 'admin':
        username = session['username']
        messages = users['admin'].get('messages', [])
        formatted_messages = []
        for msg in messages:
            if len(msg) >= 3:
                sender = msg[0]
                content = msg[1]
                timestamp = str(msg[2])[:-7] if len(msg) >= 3 else "Unknown"
                formatted_messages.append((sender, content, timestamp))
            else:
                formatted_messages.append(("Error: Invalid message format", str(msg), "Unknown"))
        return render_template('admin_dashboard.html', username=username, messages=formatted_messages)
    return redirect(url_for('login'))

@app.route('/user_logout')
def user_logout():
    session.pop('username', None)
    session.pop(blocked_websites_key, None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email'] 
        password = request.form['password']
        if username in users or any(user.get('email') == email for user in users.values()):  # Check for existing email
            error = 'Username or email already exists.'
            return render_template('register.html', error=error)
        users[username] = {'password': password, 'email': email}  
        return redirect(url_for('login'))
    return render_template('register.html', error='')

if __name__ == '__main__':
    app.run(debug=True)





