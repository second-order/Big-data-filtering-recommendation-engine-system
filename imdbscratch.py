from urllib import request
import re
import string
import time
import pymysql

conn=pymysql.connect(host='XXX',port=3306,user='XXX',passwd='XXX',db='XXX',charset='utf8')
cursor=conn.cursor()

cursor.execute("DROP TABLE IF EXISTS IMDB")
sql = """CREATE TABLE IMDB(
         TITLE  CHAR(50) NOT NULL,
         SCORE FLOAT,
         ACTORS  CHAR(255),
         COVER_URL CHAR(255),
         RUNTIME CHAR(20),
         RELEASE_DATE CHAR(20),
         TYPES CHAR(50))"""
cursor.execute(sql)

'''
https://www.imdb.com/chart/top?ref_=nv_mv_250
在右侧找到类型：action，xxx
点开
比如
https://www.imdb.com/search/title/?genres=western&sort=user_rating,desc&title_type=feature&num_votes=25000,&pf_rd_m=A2FGELUUNOQJNL&pf_rd_p
=5aab685f-35eb-40f3-95f7-c53f09d542c3&pf_rd_r=ASN95ESK00ZNEKC63WFG&pf_rd_s=right-6&pf_rd_t=15506&pf_rd_i=top&ref_=chttp_gnr_21

generes=western 。替换下方的generes
计算数量：western 包含85个title。85/50=2.将range换为2
之后会将数据发到数据库
'''

for a in range(14):
    url = 'https://www.imdb.com/search/title/?title_type=feature&num_votes=25000,&genres=sci_fi&sort=user_rating,desc&start={}&ref_=adv_nxt'.format(a*50+1)
    user_agent = 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT6.1; Trident/5.0'
    headers = {'User-Agent': user_agent}
    response = request.urlopen(url)
    html = response.read()
    html = html.decode('utf-8')

    title_pattern = re.compile(r'<div.*?class="lister-item-content">(.*?)</div>', re.S)
    picture_pattern = re.compile(r'<div.*?class="lister-item-image float-left">(.*?)</div>', re.S)
    stars_pattern=re.compile(r'Stars:(.*?)</p>',re.S)
    title_list = title_pattern.findall(html)
    picture_list = picture_pattern.findall(html)
    stars_list = stars_pattern.findall(html) 
        
    time.sleep(2)

    for i in range(50):
        title_re=re.compile(r'<a href="/title/.*?>(.*?)</a>',re.S)
        movie_title=title_re.findall(title_list[i])
        movie_title=movie_title[0]
        rate_re=re.compile(r'<strong>(.*?)</strong>',re.S)
        movie_rate=rate_re.findall(title_list[i])
        movie_rate=movie_rate[0]
        movie_rate=float(movie_rate)
        picture_re=re.compile(r'.*?loadlate="(.*?)"',re.S)
        movie_picture=picture_re.findall(picture_list[i])
        movie_picture=movie_picture[0]
        movie_picture=movie_picture.replace('.jpg','')
        type_re=re.compile('<span class="genre">(.*?)</span>',re.S)
        movie_type=type_re.findall(title_list[i])
        movie_type=''.join(movie_type[0]).replace(',',' ')
        stars_re=re.compile('<a href="/name/.*?>(.*?)</a>',re.S)
        movie_star=stars_re.findall(stars_list[i])
        movie_stars=' '.join(movie_star)
        date_re=re.compile(r'<span class="lister-item-year text-muted unbold">\((.*?)\)</span>',re.S)
        movie_date=date_re.findall(title_list[i])
        movie_date=movie_date[0]
        time_re=re.compile(r'<span class="runtime">(.*?)</span>',re.S)
        movie_time=time_re.findall(title_list[i])
        movie_time=movie_time[0]
        
        sql = "INSERT INTO IMDB(TITLE, SCORE, ACTORS, COVER_URL, RUNTIME, RELEASE_DATE, TYPES) VALUES ('%s', '%f', '%s', '%s', '%s', '%s', '%s')"%(movie_title, movie_rate, movie_stars, movie_picture, movie_time, movie_date, movie_type)
        try:
            cursor.execute(sql)
            conn.commit()
        except:
            conn.rollback()
            print ("Error: unable to fecth data")
        
        print(movie_title,movie_rate,movie_stars,movie_picture,movie_time,movie_date,movie_type)
        
conn.close()
