from flask import Flask, url_for, request, render_template, make_response, redirect
from datetime import timedelta, datetime
import hashlib
import pymysql

app = Flask(__name__)
# 配置
app.config['DEBUG'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds = 1)

now_username = None

@app.route('/')
def home(username = None):
	# 示例图片演示
	username = now_username
	# username = None
	# 查询数据库显示名字图片和星级
	db = pymysql.connect(host="192.168.137.57",user="lxk",password="lxkshp233",db = 'bigdatafilm', port = 3306, charset = 'utf8')
	cursor = db.cursor()
	sql = "select * from action limit 9"
	cursor.execute(sql)
	movielist = cursor.fetchall()
	cursor.close()
	db.close()
	return render_template('home.html', movielist = movielist)

@app.route('/search')
def search():
	movie = request.args.get('Search')
	# 要判断是谁进行的搜索
	# username = request.args.get('username')
	db = pymysql.connect(host="192.168.137.57",user="lxk",password="lxkshp233",db = 'bigdatafilm', port = 3306, charset = 'utf8')
	cursor = db.cursor()
	sql = "select * from action where title regexp '" + movie + "'"
	cursor.execute(sql)
	movielist = cursor.fetchall()
	# 关闭数据库的连接
	cursor.close()
	db.close()
	return render_template('search.html', movielist = movielist)

@app.route('/detail')
def detail():
	movie = request.args.get('movie_name')
	print(movie)
	db = pymysql.connect(host="192.168.137.57",user="lxk",password="lxkshp233",db = 'bigdatafilm', port = 3306, charset = 'utf8')
	cursor = db.cursor()
	sql = "select * from action where title='" + movie + "'"
	cursor.execute(sql)
	moviedetail = cursor.fetchall()
	# 将对应的电影名插入到用户的数据库对应项（该项不需要）
	# 
	# sql = "update users() values"
	cursor.close()
	db.close()
	return render_template('detail.html', moviedetail = moviedetail)


@app.route('/index')
def index():
	return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	if request.method == 'POST':
		if is_registerd_user(request.form['username'], request.form['password']):
			now_username = request.form['username']
			return home(request.form['username'])
        # if request.form['username'] != 'admin' or request.form['password'] != 'admin':
        #     error = 'Invalid Credentials. Please try again.'
		else:
			return redirect(url_for('home'))
	return render_template('login.html', error=error)

@app.route('/register', methods = ['GET', 'POST'])
def register():
	error = None
	if request.method == 'POST':
		# 加入是post方法提交则进入注册判断，否则直接返回注册页面
		error = correct_form_register(request.form['username'], request.form['password'], request.form['password_again'])
			# 记得要提交
		if error == None:
			return home(request.form['username'])
			# 注册成功后返回主页并且带上用户名
		else:
			# 加入错误就提示用户并且要用户重新填写
			return render_template('register.html', error = error)
	return render_template('register.html')

def correct_form_register(username, password, password_again):
	if password != password_again:
		return "两次输入的密码不一致，请重新输入"
	else:
		db = pymysql.connect(host="192.168.137.57",user="lxk",password="lxkshp233",db = 'bigdatafilm', port = 3306, charset = 'utf8')
		cursor = db.cursor()
		sql = "select * from users where username = '" + username + "'"
		if cursor.execute(sql):
			cursor.close()
			db.close()
			return "该用户名已被注册，请换一个用户名重试"
		else:
			username = request.form['username']
			password = request.form['password']
			password_digest = str(hashlib.sha256(password.encode()).hexdigest())
			sql = "insert into users values('" + username + "','" + password_digest + "', '" + datetime.now().strftime("%Y-%m-%d") + "', 0)"
			cursor.execute(sql)
			db.commit()
			cursor.close()
			db.close()
			# 加入没有问题就返回error = None
			return None


def is_registerd_user(username, password):	
	# 将username与password的hash与数据库中的值进行比对
	db = pymysql.connect(host="192.168.137.57",user="lxk",password="lxkshp233",db = 'bigdatafilm', port = 3306, charset = 'utf8')
	cursor = db.cursor()
	password_digest = str(hashlib.sha256(password.encode()).hexdigest())
	sql = "select * from users where username = '" + username + "' and password = '" + password_digest + "'"
	# 'select * from users where name = zhangsan and password = 123456789'
	if(cursor.execute(sql)):
		cursor.close()
		db.close()
		now_username = username
		return True
	else:
		cursor.close()
		db.close()
		return False
# @app.route('/<name>')
# def hello_world(name=None):
#     return render_template('hello.html', name = name)


# @app.route('/hello')
# def hello():
#     return 'Hell'

# @app.route('/user/<username>')
# def show_user_profile(username):
#     # show the user profile for that user
#     return 'User %s' % username

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         return do_the_login()
#     else:
#         return 'from'

# with app.test_request_context('/hello', method='POST'):
#     # now you can do something with the request until the
#     # end of the with block, such as basic assertions:
#     assert request.path == '/hello'
#     assert request.method == 'POST'

# if __name__ == '__main__':
#     app.run()
