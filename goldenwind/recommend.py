# coding=utf-8
from pyspark import SparkContext
from pyspark import SparkConf
from pyspark.mllib.recommendation import MatrixFactorizationModel
import sys
import time


def SetPath(sc):
    """定义全局变量Path，配置文件读取"""
    global Path
    Path = "./ALS"


def CreateSparkContext():
    """定义CreateSparkContext函数便于创建SparkContext实例"""
    sparkConf = SparkConf() \
             .setAppName("Recommend") \
             .set("spark.ui.showConsoleProgress","false")
    sc = SparkContext(conf=sparkConf)
    SetPath(sc)
    print("master="+sc.master)
    return sc


def loadModel(sc):
    """载入训练好的推荐模型"""
    try:
        model = MatrixFactorizationModel.load(sc, Path+"/ALSmodel")
        print("载入模型成功")
    except Exception:
        print("模型不存在, 请先训练模型")
    return model

def PrepareData(sc):
    """数据准备：准备u.item文件返回电影id-电影名字典（对照表）"""
     #movieTitle为dict类型
    itemRDD = sc.textFile(Path+"/u.item")
    movieTitle = itemRDD.map(lambda line: line.split("|")) \
        .map(lambda a: (int(a[0]), a[1])) \
        .collectAsMap()
    return movieTitle


#没有做去重工作，即已经打过分的电影不推荐 （不清楚recommendProducts是否自动去重，可以阅读源码/官方文档分析一下）
def RecommendUUUsers(model,movieTitle,inputname,inputcount):
    i=0
    lisa=['0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0']
    rat=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    RecommendUser = model.recommendProducts(inputname,inputcount)
    for p in RecommendUser:
        mark=str(p[2])
        mark=float(p[2])
        if mark>5:
            mark=5.000123
        namemovie=str(movieTitle[p[1]])[:-7]
        if namemovie[-5:] == ', The':
            namemovie = 'The '+namemovie[0:-5]
        lisa[i]=namemovie
        mark=mark*2
        rat[i]=round(mark,2)
        i=i+1
        lisf=[lisa,rat] 
        # lisf[0]是电影名
        # lisf[1]中是评分
    return lisf

    # i=0
    # lisa=[0,0,0,0,0,0,0,0,0]
    # RecommendUser = model.recommendProducts(inputname,inputcount)
    # for p in RecommendUser:
    #     mark=str(p[2])
    #     mark=float(p[2])
    #     if mark>5:
    #         mark=5.000123
    #     lisa[i]=p[1]
    #     i=i+1
    # return lisa
        #print(type(p[1]))   int
        #print("对编号为" + str(p[0]) + "的用户" + "推荐电影" + str(movieTitle[p[1]]) + "\n")
        #print("推荐评分为 %.1f \n"  % mark)


# if __name__ == "__main__":

def rec():
    global user_id
    global lis
    global vip
    temp_user_id = 0
    temp_vip = 0
    #sc.stop()
    # userreal=input("input userid:")
    # userreal=int(userreal)
    moviecount=9
    sc=CreateSparkContext()
    #print("==========数据准备==========")
    movieTitle = PrepareData(sc)
    print("==========载入模型==========")
    model = loadModel(sc)
    print("==========进行推荐==========")
    while True:
        # 假如和上次扫描的id相同就什么也不做
        if user_id == temp_user_id and temp_vip == vip:
            time.sleep(1)
    #Recommend(model)
        elif user_id  == temp_user_id and temp_vip != vip:
            # 更新temp_vip的值
            temp_vip = vip
            userreal = temp_user_id
            lis=RecommendUUUsers(model, movieTitle, userreal,moviecount)
            print(lis)
        elif user_id != temp_user_id and vip:
            # 更新temp_vip与用户名的值
            temp_vip = vip
            temp_user_id = user_id
            userreal = temp_user_id
            lis=RecommendUUUsers(model, movieTitle, userreal,moviecount)
            print(lis)
        else:
            time.sleep(1)
            
    # print(lis)
    # sc.stop()  #退出已有SparkContext
