import sys
import datetime
import json
from bs4 import BeautifulSoup
from http.cookiejar import MozillaCookieJar
import youtube_dl
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkCookie, QNetworkCookieJar
from PyQt5.QtCore import QUrl, QByteArray
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from argparse import ArgumentParser
from urllib.parse import urlparse

COOKIES_FILE = './cookies.txt'

def parse_args():
    # parse command arguments
    # --category: category to download
    # --slug: a course slug to download
    parser = ArgumentParser()
    parser.add_argument('--category', help='specify a category (default: ableton)')
    parser.add_argument('--slug', help='specify a course slug to download a course with the specified slug')
    parser.add_argument('--directory', help='specify a directory where downloaded videos will be added')
    args = parser.parse_args()

    # if category is not specified, make default category None
    args.category = args.category if args.category else None

    # if directory is not specified, make default directory 'current directory (./)'
    args.directory = args.directory if args.directory else './videos'

    # if directory's last character contains '/', then remove it
    args.directory = args.directory[:-1] if args.directory[-1] == '/' else args.directory

    return args

args = parse_args()

class Client(QWebEnginePage):
    def __init__(self, url):
        self.app = QApplication(sys.argv)
        QWebEnginePage.__init__(self)
        self.html = ''
        self.load_cookies('cookies.txt')
        CookieWebEngine().load()
        self.loadFinished.connect(self.on_page_load)
        self.load(QUrl(url))
        self.app.exec_()

    def on_page_load(self):
        self.html = self.toHtml(self.Callable)
        print('load finished!')

    def load_cookies(self, filename):
        with open(filename) as f:
            data = json.load(f)

        cookies = []

        for item in data:
            name = QByteArray().append(item['name'])
            value = QByteArray().append(item['value'])
            cookie = QNetworkCookie(name, value)

            if 'domain' in item:
                cookie.setDomain(item['domain'])
            if 'expirationDate' in item:
                cookie.setExpirationDate(datetime.datetime.fromtimestamp(item['expirationDate']))
            if 'hostOnly' in item:
                cookie.setHttpOnly(item['hostOnly'])
            if 'path' in item:
                cookie.setPath(item['path'])
            if 'secure' in item:
                cookie.setSecure(item['secure'])

            cookies.append(cookie)

        cookiejar = QNetworkCookieJar()
        cookiejar.setAllCookies(cookies)

        self.networkAccessManager().setCookieJar(cookiejar)

    def inser_cookie(self, cookie):
        QNetworkAccessManager().setCookieJar(cookiejar)
        print('COOKIE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

    def Callable(self, html_str):
        self.html = html_str
        self.app.quit()

class AcademyFmDownloader:
    def __init__(self):
        self.directory = args.directory
        self.base_url = 'https://academy.fm'
        self.base_category_url = self.base_url + '/courses-tutorials/'
        self.courses_url = self.base_url + '/courses'
        if args.category:
            self.category = args.category
            self.category_url = self.base_category_url + '#category=' + self.category  + '&level=all&instructor=all&type=all/'
        if args.slug:
            self.slug = args.slug
            self.course_url = self.base_url + '/courses/' + self.slug

    def get_soup(self, url=None):
        headers = {'User-Agent': 'AcademyFM Downloader'}
        response = Client(url)
        soup = BeautifulSoup(response.html, 'html.parser')
        print(soup)
        return soup

    def get_a_category(self, category_slug):
        category_soup = self.get_soup(self.base_category_url + '#category=' + category_slug  + '&level=all&instructor=all&type=all/')
        return category_soup

    def get_all_category_slugs(self):
        category_soup = self.get_soup(self.base_category_url)
        category_slugs = []
        for category in category_soup.select('.js-category-filter-item'):
            category_slugs.append(category['data-category'])
        return category_slugs

    def get_a_course(self, course_url):
        course_soup = self.get_soup(course_url)
        return course_soup;

    def get_lesson_urls(self, course_soup):
        lesson_urls = []
        lessons = course_soup.select('.main-container iframe')
        for lesson_soup in lessons:
            url = lesson_soup['src']
            lesson_urls.append(url)
        return lesson_urls

    def get_directory_name(self, category_slug, course_title):
        directory = self.directory + '/' + category_slug + '/' + course_title
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory

    def show_course_title(self, course_title):
        print('-------------------------------------------')
        print(course_title)
        print('-------------------------------------------')

    def remove_queries(self, url):
        url = self.base_url + urlparse(url).path
        return url

    def downloader(self, category_slug, course_title, lesson_urls):
        file_path = self.get_directory_name(category_slug, course_title) + '/%(autonumber)s - %(title)s.%(ext)s'
        ydl_opts = {
            'cookiefile': './cookies.txt',
            'verbose': 'true',
            # add -4 option to avoid HTTP Error 429 Too Many Requests
            # Ref: https://github.com/rg3/youtube-dl/issues/5138
            # 'force-ipv4': 'true',
            'outtmpl': file_path,
        }
        youtube_dl.utils.std_headers['Referer'] = self.base_url
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download(lesson_urls)

    def downloadAll(self):
        # loop through categories
        for category_slug in self.get_all_category_slugs():
            # get a certain category page
            category_soup = self.get_a_category(category_slug)
            # get all courses' url in a current category
            category_courses = category_soup.find_all(lambda tag: tag.name == 'div' and tag.get('class') == ['hover-bg-near-white', 'js-filter-item', 'course-entry'])
            # loop through courses in a current category
            for course_card in category_courses:
                # get the course url
                course_url = course_card.find('a')['href']
                # get the course title
                course_title = course_card.find('h4').text
                self.show_course_title(course_title);
                # get the course soup
                course_soup = self.get_a_course(course_url)
                # get the lesson urls in a current course
                lesson_urls = self.get_lesson_urls(course_soup)
                # download all lessons in the course
                self.downloader(category_slug, course_title, lesson_urls)

    def downloadSpecifiedCategory(self):
        # get a certain category page
        category_soup = self.get_a_category(self.category)
        # get all courses' url in a current category
        category_courses = category_soup.find_all(lambda tag: tag.name == 'div' and tag.get('class') == ['hover-bg-near-white', 'js-filter-item', 'course-entry'])
        # loop through courses in a current category
        for course_card in category_courses:
            # get the course url
            course_url = course_card.find('a')['href']
            # get the course title
            course_title = course_card.find('h4').text
            self.show_course_title(course_title);
            # get the course soup
            course_soup = self.get_a_course(course_url)
            # get the lesson urls in a current course
            lesson_urls = self.get_lesson_urls(course_soup)
            # download all lessons in the course
            self.downloader(self.category, course_title, lesson_urls)

    def downloadSpecifiedCourse(self):
        # get a course_url
        course_url = self.base_url + '/courses/' + self.slug
        # get the course soup
        course_soup = self.get_a_course(course_url)
        # get the category slug
        category_slug = course_soup.select_one('.cell-lesson-category.hidden-xs a').text
        # get the course title
        course_title = course_soup.select_one('.text-left .title').text
        self.show_course_title(course_title)
        # download all lessons in the course
        self.downloader(category, course_title, lesson_urls)

downloader = AcademyFmDownloader()
if args.slug:
    downloader.downloadSpecifiedCourse()
elif args.category:
    downloader.downloadSpecifiedCategory()
else:
    downloader.downloadAll()
