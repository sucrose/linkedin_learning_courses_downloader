import os
import urllib
import sys
import config
import requests
import re
import tempfile
import time

from bs4 import BeautifulSoup
from importlib import reload
from urllib.request import urlopen
from youtube_dl.utils import YoutubeDLCookieJar
try:
    from http.cookiejar import CookieJar
except ImportError:
    from cookielib import CookieJar


def login():
    cookiejar_filename = './cookies.txt'
    cookiejar = YoutubeDLCookieJar(cookiejar_filename)
    cookiejar.load(ignore_discard=True, ignore_expires=True)
    try:
        auth_cookie = cookiejar._cookies['.www.linkedin.com']['/']['li_at'].value
    except:
        sys.exit(0)

    temp_file = tempfile.NamedTemporaryFile(delete=False)
    try:
        cookiejar.save(filename=temp_file.name, ignore_discard=True, ignore_expires=True)
        # temp = temp_file.read().decode('utf-8')
        # test.assertTrue(re.search(r'li_at', temp))
    finally:
        temp_file.close()
        #os.remove(temp_file.name)

    return auth_cookie


def load_page(opener, url, data=None):
    try:
        response = opener.open(url)
    except:
        print('[!] Rate limited')

    try:
        if data is not None:
            response = opener.open(url, data)
        else:
            response = opener.open(url)
        return ''.join(response.readlines())
    except:
        print('[Notice] Exception hit')
        sys.exit(0)


def download_file(url, file_path, file_name):
    reply = requests.get(url, stream=True)
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    with open(file_path + '/' + file_name, 'wb') as f:
        for chunk in reply.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)


if __name__ == '__main__':
    try:
        session = login()
        if len(session) == 0:
            sys.exit('[!] Unable to obtain a valid authenticated session')
        print('[*] Successfully obtained valid authenticated session: %s' % session)
        cookies = dict(li_at = session)
    except Exception(e):
        sys.exit('[!] Error: %s' % e)

    headers = {'Csrf-Token':'ajax:4332914976342601831'}
    cookies['JSESSIONID'] = 'ajax:4332914976342601831'

    for course in config.COURSES:
        print('')
        course_url = 'https://www.linkedin.com/learning-api/detailedCourses' \
                     '??fields=videos&addParagraphsToTranscript=true&courseSlug={0}&q=slugs'.format(course)
        r = requests.get(course_url, cookies=cookies, headers=headers)
        course_name = r.json()['elements'][0]['title']
        course_name = re.sub(r'[\\/*?:"<>|]', "", course_name)
        chapters = r.json()['elements'][0]['chapters']
        print('[*] Parsing "%s" course\'s chapters' % course_name)
        print('[*] [%d chapters found]' % len(chapters))
        for chapter in chapters:
            chapter_name = re.sub(r'[\\/*?:"<>|]', "", chapter['title'])
            videos = chapter['videos']
            vc = 0
            print('[*] --- Parsing "%s" chapters\'s videos' % chapter_name)
            print('[*] --- [%d videos found]' % len(videos))
            for video in videos:
                video_name = re.sub(r'[\\/*?:"<>|]', "", video['title'])
                video_slug = video['slug']
                video_url = 'https://www.linkedin.com/learning-api/detailedCourses' \
                            '?addParagraphsToTranscript=false&courseSlug={0}&q=slugs&resolution=_720&videoSlug={1}'\
                    .format(course, video_slug)
                r = requests.get(video_url, cookies=cookies, headers=headers)
                vc += 1
                try:
                    download_url = re.search('"progressiveUrl":"(.+)","streamingUrl"', r.text).group(1)
                except:
                    print('[!] ------ Can\'t download the video "%s", probably is only for premium users' % video_name)
                else:
                    print('[*] ------ Downloading video "%s"' % video_name)
                    download_file(download_url, 'out/%s/%s' % (course_name, chapter_name), '%s. %s.mp4' % (str(vc), video_name))
                    time.sleep(10)