import threading
import requests
import time

class Mt(object):
    def __init__(self):
        self.living_thread = 0
        self.has_down_size = 0
        self.new_down_size = 0
        self.file_length = 0
        self.lock_down_size = threading.Lock()
        self.lock_thread_num = threading.Lock()
        self.url = ''
        self.filepath = ''
        self.filename = ''
        self.headers = None
        self.thread_id = 0
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

        tf = open(filepath+filename,'wb')
        tf.truncate(self.file_length)
        tf.close()

        slice_len = self.file_length // thread_num

        if self.start:
            self.start(self.file_length,thread_num,filename)

        td = 0
        for th in range(0,thread_num):
            start  = th * slice_len
            if th == thread_num - 1:
                end = self.file_length
            else:
                end = start + slice_len
            td += 1
            t = threading.Thread(target=self.handler, kwargs={'start':start, 'end':end, 'headers':self.headers, 'td': td})
            t.setDaemon(True)
            t.start()

        if self.percent:
            self.percent(self.thread_id,
                         int((self.has_down_size * 100) / self.file_length),
                         self.living_thread)

        while self.living_thread > 0:
            time.sleep(1)
        if self.success:
            self.success(self.thread_id, self.url)
        pass

    def handler(self, start, end, headers, td):
        bstart = start
        headers = headers.copy()
        this_down = 0
        while True:
            try:
                headers['range'] = 'bytes={0}-{1}'.format(start, end)
                while True:
                    try:
                        r = requests.get(self.url,headers=headers, stream=True, timeout=2)
                        break
                    except Exception as e:
                        continue
                if r.status_code != 206:
                    print('{}:Thread in {}'.format(r.status_code, self.url))
                    break
                chunk_size = 1024
                with open(self.filepath+self.filename,'r+b') as tf:
                    tf.seek(start)
                    for chunk in r.iter_content(chunk_size):
                        self.lock_down_size.acquire()
                        this_down += len(chunk)
                        start += len(chunk)
                        self.new_down_size += len(chunk)
                        self.has_down_size += len(chunk)
                        if self.new_down_size >= self.file_length / 100:
                            if self.percent:
                                self.percent(self.thread_id,
                                             int((self.has_down_size * 100) / self.file_length),
                                             self.living_thread)
                            self.new_down_size = 0
                        self.lock_down_size.release()
                        tf.write(chunk)
                if start < end:
                    continue
                break
            except:
                # print('A Thread Timeout in {}, Redo it, id = {} start from {}, next start at{}'
                #      .format(self.filename, td, bstart, start))
                continue

        self.lock_thread_num.acquire()
        self.living_thread -= 1
        # print('In {} id={} Task {}/{}=={}'.
        #      format(self.filename, td, this_down, end - bstart, int(this_down*100/(end - bstart))))
        self.lock_thread_num.release()
        if self.percent:
            self.percent(self.thread_id,
                         int((self.has_down_size * 100) / self.file_length),
                         self.living_thread)
        pass
