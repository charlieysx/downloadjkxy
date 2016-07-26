    downloadjkxy.py

#####这是一个爬取极客学院视频的python爬虫
#####注：需要有会员的帐号才能下载
---
* ###相关的类
 * FormatChar 是处理字符/字符串的类
 * Crawler 是爬虫类，主要是用来登录极客学院跟下载视频
 * CourseUrlsThread 是获取课程网址的线程类


* ###使用方法
 * 初始化：crawler = Crawler('用户名', '密码', '视频保存地址')
 * 登录：result = crawler.login()
 * 获取要下载的页面中的课程网址：crawler.getCourseUrls('http://www.jikexueyuan.com/course/android/?pageNum=', 11)后面的11是有11个页面的意思
 * 下载视频：crawler.download(workQueue.get())
 
大概方法就是这样，详细看代码。

QQ：249900679
