#多线程下载小工具
import threading
import requests
import time

"""
通过注册register_start,register_percent,register_success
即@register_start，@register_percent...来修饰你的函数，也可以不用注册
可以回调你需要的函数
"""

class Mt(object):
    def __init__(self):
        #线程数
        self.living_thread = 0
        #已下字节
        self.has_down_size = 0
        #新下的字节
        self.new_down_size = 0
        #文件长度
        self.file_length = 0
        #锁
        self.lock_down_size = threading.Lock()
        self.lock_thread_num = threading.Lock()
        #url
        self.url = ''
        #文件路径
        self.filepath = ''
        #文件名
        self.filename = ''
        #请求头
        self.headers = None
        #进程id
        self.thread_id = 0
        #回调
        self.success = None
        self.percent = None
        self.start = None

    def register_start(self, func):
        self.start = func
        return func

    def register_success(self, func):
        self.success = func
        return func

    def register_percent(self, func):
        self.percent = func
        return func

    def set_thread_id(self, thread_id):

        self.thread_id = thread_id

    def mt_download(self, url, filepath, filename, thread_num, headers):
        self.living_thread = thread_num
        self.url = url
        self.filepath = filepath
        self.filename = filename
        self.headers = headers.copy()
        try:
            h = requests.head(url,headers = headers)
            self.file_length = int(h.headers['content-length'])
        except Exception as e:
            print(e)
            return
        #创建文件
        tf = open(filepath+filename,'wb')
        tf.truncate(self.file_length)
        tf.close()
        #分片
        slice_len = self.file_length // thread_num
        
        if self.start:
            self.start(self.file_length,thread_num,filename)
        #开始下载
        for th in range(0,thread_num):
            start  = th * slice_len
            if th == thread_num - 1:
                end = self.file_length
            else:
                end = start + slice_len
            t = threading.Thread(target=self.handler, kwargs={'start':start, 'end':end, 'headers':self.headers})
            t.setDaemon(True)
            t.start()
        #本线程休眠，等待子线程结束
        while self.living_thread > 0:
            time.sleep(1)
        if self.success:
            self.success(self.thread_id)
        pass

    def handler(self, start, end, headers):
        #请求头修改
        headers = headers.copy()
        headers['range'] = 'bytes={0}-{1}'.format(start, end)
        while True:
            try:
                r = requests.get(self.url,headers = headers, stream=True, timeout = 3000)
                break
            except:
                continue
        #下载，计算下载长度
        chunk_size = 10240
        with open(self.filepath+self.filename,'r+b') as tf:
            while True:
                try:
                    tf.seek(start)
                    for chunk in r.iter_content(chunk_size):
                        tf.write(chunk)
                        self.lock_down_size.acquire()
                        self.new_down_size += len(chunk)
                        self.has_down_size += len(chunk)
                        #如果新下载的字节达到1%，调用percent
                        if self.new_down_size >= self.file_length / 100:
                            if self.percent:
                                self.percent(self.thread_id,
                                             int((self.has_down_size * 100) / self.file_length),
                                             self.living_thread)
                            self.new_down_size = 0
                        self.lock_down_size.release()
                    break
                except:
                    continue
        #活动线程减1
        self.lock_thread_num.acquire()
        self.living_thread -= 1
        self.lock_thread_num.release()
        pass
