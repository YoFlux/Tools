import mt_download as Mt

mt = Mt.Mt()
mt.set_thread_id(Name)
Url = ''
base_path = ''
Name = ''
headers = {}

@mt.register_start
def start(file_len, thread_num, filename):
    print('start')

@mt.register_success
def success(thread_id, t_url):
    print('下载完成')

@mt.register_percent
def percent(thread_id, p, living_thread_num):
    print('percent')

t = threading.Thread(target=mt.mt_download,
                     kwargs={'url': Url, 'filepath': base_path,
                             'filename': Name, 'thread_num': 10, 'headers': headers})
t.setDaemon(True)
t.start()