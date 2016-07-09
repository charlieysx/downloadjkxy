# coding:utf-8

import urllib.request
import urllib.parse
import os
import sys
import threading
import http.cookiejar
import re
import queue
import time

# 处理字符的类
class FormatChar:
    # 创建文件或文件夹夹不可用的字符
    NO_USE = '/\\:*?"<>|'

    # 判断是否是符合文件或文件夹命名规范的字符
    def is_Mkdirable(self, uchar):
    	if uchar in self.NO_USE:
    		return False
    	else:
    		return True
    
    # 判断uchar是否是汉字
    def is_Chinese(self, uchar):
        if uchar >= u'\u4e00' and uchar <= u'\u9fa5':
            return True
        else:
            return False

    # 判断是否是可打印字符
    def is_Printable(self, uchar):
        if uchar >= ' ' and uchar <= '~':
        	return True
        else:
        	return False

    # 把全角字符转为半角字符，因为课程名称有些是用中文括号什么的
	# 不先转为半角的括号等，在判断打印字符时会被过滤掉
    def Q2B(self, uchar):
        inside_code=ord(uchar)
        if inside_code == 0x3000:
            inside_code = 0x0020
        else:
            inside_code -= 0xfee0

        if inside_code < 0x0020 or inside_code > 0x7e:
            return uchar

        return chr(inside_code)

	# 因为课程名可能包含全角等符号，而且关于字符判断有多个
	# 所以写多个方法综合判断
    def Analysis_uchar(self, uchar):
        newchar = self.Q2B(uchar)
        if (self.is_Chinese(uchar) or self.is_Printable(newchar)) and self.is_Mkdirable(newchar):
            return True
        else:
            return False

	
	# 分析整个字符串并返回处理好的字符串
    def Analysis_str(self, string):
        return "".join([s for s in string if self.Analysis_uchar(s)])

# 获取网址的线程类
class CourseUrlsThread(threading.Thread):
	def __init__(self, url, q, i):
		threading.Thread.__init__(self)
		self.url = url
		self.q = q
		self.i = i

	def run(self):
		print('开始---获取第%d页的课程网址...' % self.i)
		request = urllib.request.Request(self.url)
		# 给一个useragent
		request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36')
		request = urllib.request.urlopen(request)
		html = request.read().decode('utf-8')
		request.close()
		courseUrls = re.findall(r'class="lesson-info-h2"><a href="(.*?)"', html)
		queueLock.acquire()
		for courseUrl in courseUrls:
			self.q.put(courseUrl)

		threads.remove(self)
		queueLock.release()
		print('结束---第%d页的课程网址已获取...' % self.i)
		time.sleep(1)

# 爬虫类
class Crawler:
	# 用于登录极客学院的用户名和密码
	__username = ''
	__password = ''
	# 用于保存视频的总路径
	__folderPath = ''


	def __init__(self, name, pawd, path):
		self.__username = name
		self.__password = pawd
		self.__folderPath = path

        # 初始化一个CookieJar来处理Cookie
		cookieJar = http.cookiejar.CookieJar()
		# 实例化一个全局opener
		opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookieJar))
		# 把这个cookie处理机制装上去,大概是这个意思-.-
		urllib.request.install_opener(opener)

		# 判断文件夹是否存在
		folderExists = os.path.exists(self.__folderPath)
		if not folderExists:
			os.mkdir(self.__folderPath)

	# 输出字符串
	def printstr(self, str1):
		le = len(str1)

		for c in str1:
			if FormatChar().is_Chinese(c):
				le += 1

		i = 0
		self.length = le + 6

		while i < self.length:
			i += 1
			print('-', end = '')

		print('')

		print('|  ' + str1, end = '')
		print('  |')

		i = 0
		while i < self.length:
			i += 1
			print('-', end = '')

		print('')

	# 登陆函数
	def login(self):
		# 从登录页面获取登陆参数
		login_url = 'http://passport.jikexueyuan.com/sso/login'
		# 登陆信息发送到这个地址
		passport_url = 'http://passport.jikexueyuan.com/submit/login?is_ajax=1'
		
		# 获取登陆页面源码
		# request = urllib.request.urlopen(login_url)
		request = urllib.request.Request(login_url)
		# 给一个useragent
		request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36')
		request = urllib.request.urlopen(request)
		html = request.read().decode('utf-8')
		request.close()
		
		# 获取登陆要post的数据
		expire = re.search(r"(?s)value='(.*?)' name='expire",html)
		
		data = {
			'expire': expire.group(1),
			'referer': 'http%3A%2F%2Fwww.jikexueyuan.com%2F',
			'uname': self.__username, # 用户名
			'password': self.__password, # 密码
			'verify': '', # 验证码，其实为空也能登录成功
		}
		post_data = urllib.parse.urlencode(data)
		
		post_data = bytes(post_data, 'utf-8')
		# print(type(post_data))
		request = urllib.request.Request(passport_url, post_data)
		# 给一个useragent
		request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36')
		# 发送登录请求
		request = urllib.request.urlopen(request)
		html = request.read().decode('utf-8')
		request.close()

		return html

	# 获取视频总网址
	def getCourseUrls(self, startUrl, page):

		# 最多开4个线程
		moreThread = 4
		p = 1
		while p <= page:
			# len = threading.activeCount()
			# if(len == moreThread):
			# 	continue
			if len(threads) == moreThread:
				continue
			thread = CourseUrlsThread(startUrl + str(p), workQueue, p)
			thread.start()
			threads.append(thread)
			p += 1

	# 视频下载方法
	def download(self, courseUrl):
		# 获取课程名称
		request = urllib.request.Request(courseUrl)
		# 给一个useragent
		request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36')
		request = urllib.request.urlopen(request)
		coursePageHtml = request.read().decode('utf-8')
		request.close()
		courseName = re.search(r'(?s)<title>(.*?)-', coursePageHtml).group(1)

		courseName = FormatChar().Analysis_str(courseName)

		# 课程数量
		courseCount = int(re.search(r'(?s)class="timebox"><span>(.*?)课时',coursePageHtml).group(1))
		# 存储视频的文件夹路径
		__folderPath = self.__folderPath + courseName + '/'
		# 判断文件夹是否存在
		folderExists = os.path.exists(__folderPath)
		if not folderExists:
			try:
				os.mkdir(__folderPath)
			except:
				print(courseName + "--------文件夹创建失败")
				return 
		
		print('课程名:' + courseName + ' 视频数量:' + str(courseCount))
		# 课程的编号,构建课程的页面地址
		i = 0
		while i < courseCount:
			i += 1
			pageUrl = courseUrl.split('.html')[0] + '_' + str(i) + '.html?ss=1'
			# 本节课程的html代码

			request = urllib.request.Request(pageUrl)
			# 给一个useragent
			request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36')
			request = urllib.request.urlopen(request)
			pageHtml = request.read()
			# ht = pageHtml
			# ff = open('web.txt','wb+')
			# ff.write(ht)
			# ff.close()
			request.close()
			pageHtml = pageHtml.decode('utf-8')

			# 本节课程的名称
			name = re.search(r'(?s)<title>(.*?)-',pageHtml).group(1)
			name = FormatChar().Analysis_str(name)

			if os.path.isfile(__folderPath + str(i) + name + '.mp4'):
				print(__folderPath + str(i) + name + '.mp4-----视频已存在')
				continue

			# print(name + '下载中...')
			# 本节课程的视频地址
			videoUrl = re.search(r'<source src="(.*?)"',pageHtml)
			# print(videoUrl)
			# 有的页面写的课时比实际课时多,会匹配不到视频地址
			if videoUrl == None:
				continue
			else:
				videoUrl = videoUrl.group(1)
			
			str1 = '正在下载视频' + str(i) + ' : ' + name
			self.printstr (str1)

			# 存储视频的Path: 总路径/课程名/每一节的名称
			urllib.request.urlretrieve(videoUrl, __folderPath + str(i) + name + '.mp4', self.reporthook)
		# print ('下载完成')

	# 回调函数，显示下载进度
	def reporthook(self, blocknum, blocksize, totalsize):
		'''回调函数
    	@blocknum: 已经下载的数据块
    	@blocksize: 数据块的大小
    	@totalsize: 远程文件的大小
    	'''
		percent = 100.0 * blocknum * blocksize / totalsize
		if percent > 100:
			percent = 100
		downsize = blocknum * blocksize
		if downsize >= totalsize:
			downsize = totalsize

		l = 0
		s = '['
		while l <= int(self.length * percent / 100):
			s += "="
			l += 1
		l = 0
		s += ">"
		while l <= int(self.length * (100 - percent) / 100):
			s += " "
			l += 1
		s += "]%.2f%%---" % (percent)
		s += "%.2f" % (downsize / 1024 / 1024) + "M/" + "%.2f" % (totalsize / 1024 / 1024) + "M \r"
		sys.stdout.write(s)
		sys.stdout.flush()
		if percent == 100:
			print('')


threads = []
queueLock = threading.Lock()
workQueue = queue.Queue(1000)


if __name__ == "__main__":
	# print(threading.activeCount())
	# 注：改爬虫下载需要有会员的用户
	crawler = Crawler('用户名', '密码', '保存下载后的视频的地址')
	result = crawler.login()
	if re.search('登录成功', result) != None:
		print('登录成功...')

		# 第二个参数为多少个页面
		crawler.getCourseUrls('http://www.jikexueyuan.com/course/android/?pageNum=', 11)

		# 等待所有线程完成，即所有课程网址获取结束
		for t in threads:
			t.join()

		print('----------' + str(workQueue.qsize()) + '个课程----------')
		n = 1
		while not workQueue.empty():
			print('下载第%d个课程---' % n, end='')
			n += 1
			crawler.download(workQueue.get())
			time.sleep(1)

	else:
		print('登录失败...')


