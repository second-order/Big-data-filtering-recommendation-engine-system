# coding=utf-8
from flask import Flask, url_for, request, render_template, make_response, redirect
from flask_cors import *
from datetime import timedelta, datetime
import hashlib
import pymysql
import re
import recommend
import threading
import time

app = Flask(__name__)
# 配置
app.config['DEBUG'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds = 1)
# 解决跨域问题：No 'Access-Control-Allow-Origin' header is present on the requested resource.
CORS(app, supports_credentials=True)
# 解决中文显示的问题
app.config['JSON_AS_ASCII'] = False


now_username=None
vip=0
user_id=0
# 推荐电影编号
lis=[]
t1=None
is_load = False


@app.route('/')
def home():
	# 示例图片演示
	global now_username
	global vip
	global user_id
	global lis
	global t1
	global is_load
	# 启动预测模型
	print("线程个数"+str(threading.active_count()))
	if t1:
		print(1)
	else:
		t1 = threading.Thread(target=tuijian)
		t1.start()

	username = now_username
	# username = None
	# 查询数据库显示名字图片和星级
	if vip:
		# 避免模型未载入就进入到后续处理逻辑
		while not is_load:
			time.sleep(1)
		# 避免推荐之前就跳转到home
		time.sleep(1)
		res_lis = []
		db = pymysql.connect(host="129.28.17.220",user="lxk",password="BxBCXNwJdLHpRsxi",db = 'bigdatafilm', port = 3306, charset = 'utf8')
		cursor = db.cursor()
		for lis_index in range(len(lis[0])):
			lis_name = lis[0][lis_index]
			# print(lis_name)
			cursor.execute("select * from IMDB where title=%s", lis_name)
			a = cursor.fetchall()
			if a == ():
				pass
			else:
				# print(a)
				temp_res_lis = list(a[0])
			# 将评分修改为推荐评分
				temp_res_lis[1] = lis[1][lis_index]
				res_lis.append(temp_res_lis)
		movielist = res_lis
		movienum = len(movielist)
		# print(movielist)
		cursor.close()
		db.close()
		return render_template('home.html', movielist = movielist, username = username, movienum = movienum)
	else:
		db = pymysql.connect(host="129.28.17.220",user="lxk",password="BxBCXNwJdLHpRsxi",db = 'bigdatafilm', port = 3306, charset = 'utf8')
		cursor = db.cursor()
		sql = "select * from total limit 9"
		cursor.execute(sql)
		movielist = cursor.fetchall()
		# print(movielist)
		cursor.close()
		db.close()
		movienum = len(movielist)
		return render_template('home.html', movielist = movielist, username = username, movienum = movienum)

# 新建线程运行推荐算法
def tuijian():
	global vip
	global user_id
	global lis
	global is_load
	temp_user_id = 0
	temp_vip = 0
	# sc.stop()
	# userreal=input("input userid:")
	# userreal=int(userreal)
	moviecount=36
	sc=recommend.CreateSparkContext()
	#print("==========数据准备==========")
	movieTitle = recommend.PrepareData(sc)
	print("==========载入模型==========")
	model = recommend.loadModel(sc)
	print("==========进行推荐==========")
	is_load = True
	while True:
		# 假如和上次扫描的id相同就什么也不做
		if user_id == temp_user_id and temp_vip == vip:
			time.sleep(1)
	#Recommend(model)
		elif user_id  == temp_user_id and temp_vip != vip:
			# 更新temp_vip的值
			temp_vip = vip
			userreal = temp_user_id
			lis=recommend.RecommendUUUsers(model, movieTitle, userreal,moviecount)
			print(lis)
		elif user_id != temp_user_id and vip:
			# 更新temp_vip与用户名的值
			temp_vip = vip
			temp_user_id = user_id
			userreal = temp_user_id
			lis=recommend.RecommendUUUsers(model, movieTitle, userreal,moviecount)
			print(lis)
		else:
			time.sleep(1)


@app.route('/search')
def search():
	global now_username
	movie = request.args.get('Search')
	# 要判断是谁进行的搜索
	# username = request.args.get('username')
	db = pymysql.connect(host="129.28.17.220",user="lxk",password="BxBCXNwJdLHpRsxi",db = 'bigdatafilm', port = 3306, charset = 'utf8')
	cursor = db.cursor()
	# sql = "select * from total where title regexp '" + movie + "'"
	cursor.execute("select * from total where title regexp %s", (movie))
	movielist = list(cursor.fetchall())
	cursor.execute("select * from IMDB where title regexp %s", (movie))
	if movielist == ():
		movielist = movielist[1:]
	movielist += list(cursor.fetchall())
	movienum = len(movielist)
	# 关闭数据库的连接
	cursor.close()
	db.close()
	return render_template('search.html', movielist = movielist, movienum = movienum, username = now_username)

@app.route('/detail', methods=['GET', 'POST'])
def detail():
	global now_username
	global vip
	movie = request.args.get('movie_name')
	if request.method == 'POST':
		score = request.form['score']
		db = pymysql.connect(host="129.28.17.220",user="lxk",password="BxBCXNwJdLHpRsxi",db = 'bigdatafilm', port = 3306, charset = 'utf8')
		cursor = db.cursor()
		cursor.execute("select score_records from users where username=%s", now_username)
		oldstr = cursor.fetchall()[0][0]
		print(oldstr)
		newstr = update_score(oldstr, movie, score)
		print(newstr)
		cursor.execute("update users set score_records=%s where username=%s", (newstr,now_username))
		# 修改用户评分之后提交
		db.commit()
		cursor.execute("select * from total where title=%s", (movie))
		# 之后要跳转回原来的详情页
		moviedetail = list(cursor.fetchall())
		cursor.execute("select * from IMDB where title regexp %s", (movie))
		if moviedetail == ():
			moviedetail = moviedetail[1:]
		moviedetail += list(cursor.fetchall())
		cursor.close()
		db.close()
		return render_template('detail.html', moviedetail = moviedetail, username=now_username, vip = vip)

	db = pymysql.connect(host="129.28.17.220",user="lxk",password="BxBCXNwJdLHpRsxi",db = 'bigdatafilm', port = 3306, charset = 'utf8')
	cursor = db.cursor()
	# sql = "select * from total where title='" + movie + "'"
	# cursor.execute("select * from total where title=%s", (movie))
	# moviedetail = cursor.fetchall()
	cursor.execute("select * from total where title=%s", (movie))
	moviedetail = list(cursor.fetchall())
	cursor.execute("select * from IMDB where title regexp %s", (movie))
	if moviedetail == ():
		moviedetail = moviedetail[1:]
	moviedetail += list(cursor.fetchall())
	# 将对应的电影名插入到用户的数据库对应项（该项不需要）
	# 
	# sql = "update users() values"
	cursor.close()
	db.close()
	return render_template('detail.html', moviedetail = moviedetail, username=now_username, vip = vip)

def update_score(oldstr, movie_name, movie_score):
	beforestr = movie_name+r'.*?;'
	# print(beforestr)
	# print(type(beforestr))
	afterstr = movie_name+r':'+str(movie_score)+r';'
	# print(afterstr)
	# print(type(afterstr))
	# print(oldstr)
	# print(type(oldstr))
	newstr = re.sub(beforestr,afterstr,oldstr)
	# 加入没有找到这个电影就直接在字符串后添加
	if oldstr == newstr:
		newstr = oldstr+movie_name+r':'+movie_score+';'
		# print(222)
	return newstr

@app.route('/index')
def index():
	return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	global now_username
	error = None
	if request.method == 'POST':
		if is_registerd_user(request.form['username'], request.form['password']):
			now_username = request.form['username']
			return home()
        # if request.form['username'] != 'admin' or request.form['password'] != 'admin':
        #     error = 'Invalid Credentials. Please try again.'
		else:
			return redirect(url_for('home'))
	return render_template('login.html', error=error)

@app.route('/register', methods = ['GET', 'POST'])
def register():
	global now_username
	global user_id
	global vip
	error = None
	if request.method == 'POST':
		# 加入是post方法提交则进入注册判断，否则直接返回注册页面
		error = correct_form_register(request.form['username'], request.form['password'], request.form['password_again'])
			# 记得要提交
		if error == None:
			now_username = request.form['username']
			print(now_username)
			db = pymysql.connect(host="129.28.17.220",user="lxk",password="BxBCXNwJdLHpRsxi",db = 'bigdatafilm', port = 3306, charset = 'utf8')
			cursor = db.cursor()
			cursor.execute("select * from users where username = %s", now_username)
			user_id = cursor.fetchall()[0][5]
			vip = 0
			return home()
			# 注册成功后返回主页并且带上用户名
		else:
			# 加入错误就提示用户并且要用户重新填写
			return render_template('register.html', error = error)
			# 假如创建用户之后删除再创建id仍然会递增
	return render_template('register.html')

@app.route('/pay', methods = ['GET', 'POST'])
def pay():
	global now_username
	db = pymysql.connect(host="129.28.17.220",user="lxk",password="BxBCXNwJdLHpRsxi",db = 'bigdatafilm', port = 3306, charset = 'utf8')
	cursor = db.cursor()
	cursor.execute("select * from users where username = %s", now_username)
	now_time = str(cursor.fetchall()[0][3])
	error = None
	if request.method == 'POST':
		if now_username == None:
			error = "请先登录"
		else:
			error = correct_pay(request.form['password'], str(int(request.form['time'])+int(now_time)))
		if error == None:
			time.sleep(1)
			return home()
		else:
			return render_template('pay.html', error = error, now_time = now_time)
	return render_template('pay.html', error = error, now_time = now_time)


def correct_pay(password, time):
	global now_username
	global vip
	db = pymysql.connect(host="129.28.17.220",user="lxk",password="BxBCXNwJdLHpRsxi",db = 'bigdatafilm', port = 3306, charset = 'utf8')
	cursor = db.cursor()
	password_digest = str(hashlib.sha256(password.encode()).hexdigest())
	if(cursor.execute("select * from users where username = %s and password = %s", (now_username, password_digest))):
		cursor.execute("update users set VIP_days_left =%s", time)
		db.commit()
		vip = int(time)
		cursor.close()
		db.close()
		return None
	else:
		return "请输入正确的密码以验证身份"



def correct_form_register(username, password, password_again):
	if password != password_again:
		return "两次输入的密码不一致，请重新输入"
	else:
		db = pymysql.connect(host="129.28.17.220",user="lxk",password="BxBCXNwJdLHpRsxi",db = 'bigdatafilm', port = 3306, charset = 'utf8')
		cursor = db.cursor()
		# sql = "select * from users where username = '" + username + "'"
		if cursor.execute("select * from users where username = %s", (username)):
			cursor.close()
			db.close()
			return "该用户名已被注册，请换一个用户名重试"
		else:
			username = request.form['username']
			password = request.form['password']
			password_digest = str(hashlib.sha256(password.encode()).hexdigest())
			# sql = "insert into users values('" + username + "','" + password_digest + "', '" + datetime.now().strftime("%Y-%m-%d") + "', 0)"
			cursor.execute("insert into users(username, password, vip_starting_time) values(%s, %s, %s)", (username, password_digest, datetime.now().strftime("%Y-%m-%d")))
			db.commit()
			cursor.close()
			db.close()
			# 加入没有问题就返回error = None
			return None


def is_registerd_user(username, password):	
	global vip
	global user_id
	# 将username与password的hash与数据库中的值进行比对
	db = pymysql.connect(host="129.28.17.220",user="lxk",password="BxBCXNwJdLHpRsxi",db = 'bigdatafilm', port = 3306, charset = 'utf8')
	cursor = db.cursor()
	password_digest = str(hashlib.sha256(password.encode()).hexdigest())
	# sql = "select * from users where username = '" + username + "' and password = '" + password_digest + "'"
	# 'select * from users where name = zhangsan and password = 123456789'
	if(cursor.execute("select * from users where username = %s and password = %s", (username, password_digest))):
		# cursor.execute("select * from users where username = %s and password = %s", (username, password_digest))
		user_message = cursor.fetchall()
		# cursor.fetchall之后cursor未空
		vip = user_message[0][3]
		user_id = int(user_message[0][5])
		cursor.close()
		db.close()
		# now_username = username
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

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000)
