from bs4 import BeautifulSoup
import requests
import os
from argparse import ArgumentParser
from config import ACCOUNT
from urllib.parse import urlparse

def parse_args():
    # parse command arguments
    # --category: category to download
    # --slug: a course slug to download
    parser = ArgumentParser()
    parser.add_argument('--mastercourse', help='specify a mastercourse (default: ableton)')
    parser.add_argument('--slug', help='specify a slug to download a course with the specified slug')
    parser.add_argument('--directory', help='specify a directory where downloaded videos will be added')
    args = parser.parse_args()

    # if technology is not specified, make default category None
    args.mastercourse = args.mastercourse if args.mastercourse else None

    # if directory is not specified, make default directory 'current directory (./)'
    args.directory = args.directory if args.directory else './videos'

    # if directory's last character contains '/', then remove it
    args.directory = args.directory[:-1] if args.directory[-1] == '/' else args.directory

    return args

args = parse_args()

class AcademyFmDownloader:
    def __init__(self):
        self.directory = args.directory
        self.base_url = 'https://academy.fm'
        self.courses_url = self.base_url + '/courses'
        if args.technology:
            self.technology = args.technology
            self.technologies_url = self.base_url + '/technologies/' + self.technology
        if args.slug:
            self.slug = args.slug
            self.course_url = self.base_url + '/courses/' + self.slug

    def get_soup(self, url=None):
        result = requests.get(url)
        c = result.content
        soup = BeautifulSoup(c, 'html.parser')
        return soup

    def get_a_technology(self, slug):
        technology_url = self.base_url + '/technologies/' + slug
        technology_soup = self.get_soup(technology_url)
        return technology_soup

    def get_all_technology_slugs(self):
        courses_soup = self.get_soup(self.courses_url)
        technology_slugs = []
        for tech in courses_soup.select('.anchor-to-technology'):
            technology_slugs.append(tech['data-technology'])
        return technology_slugs

    def get_a_course(self, course_url):
        course_soup = self.get_soup(course_url)
        return course_soup;

    def get_directory_name(self, technology_slug, course_title):
        directory = self.directory + '/videos/' + technology_slug + '/' + course_title
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

    def get_tech_slug(self, course_soup):
        tech_slug = course_soup.select('.cell-lesson-category.hidden-xs a').text()
        return tech_slug

    def download_via_egghead_downloader(self, technology_slug, course_title, url):
        file_path = self.get_directory_name(technology_slug, course_title) + '/'
        command = (
            "youtube-dl" +
            " -e " + ACCOUNT['username'] +
            " -p " + ACCOUNT['password'] +
            " -c " + url + " " + '"' + file_path + '"'
        )
        os.system(command)

    def downloadAll(self):
        # loop through technologies
        for tech_slug in self.get_all_technology_slugs():
            # get a certain technology page
            tech_soup = self.get_a_technology(tech_slug)
            # get all courses' url in a current technology
            tech_courses = tech_soup.find_all('div', { 'class': 'card-course' })
            # loop through courses in a current technology
            for course_card in tech_courses:
                # get the course url
                course_url = course_card.find('a', { 'class': 'link-overlay' })['href']
                course_url = self.base_url + course_url
                # get the course title
                course_title = course_card.find('h3').text
                self.show_course_title(course_title);
                # get the course soup
                course_soup = self.get_a_course(course_url)
                # get the lesson urls in a current course
                lessons = course_soup.select('.cell-lesson-title')
                # download all lessons in the course
                self.download_via_egghead_downloader(tech_slug, course_title, course_url)


    def downloadSpecifiedTechnology(self):
        # get a certain technology page
        tech_soup = self.get_a_technology(self.technology)
        # get all courses' url in a current technology
        tech_courses = tech_soup.find_all('div', { 'class': 'card-course' })
        # loop through courses in a current technology
        for course_card in tech_courses:
            # get the course url
            course_url = course_card.find('a', { 'class': 'link-overlay' })['href']
            course_url = self.base_url + course_url
            # get the course title
            course_title = course_card.find('h3').text
            self.show_course_title(course_title);
            # get the course soup
            course_soup = self.get_a_course(course_url)
            # download all lessons in the course
            self.download_via_egghead_downloader(self.technology, course_title, course_url)

    def downloadSpecifiedCourse(self):
        # get a course_url
        course_url = self.base_url + '/courses/' + self.slug
        # get the course soup
        course_soup = self.get_a_course(course_url)
        # get the technology slug
        tech_slug = course_soup.select_one('.cell-lesson-category.hidden-xs a').text
        # get the course title
        course_title = course_soup.select_one('.text-left .title').text
        self.show_course_title(course_title)
        # download all lessons in the course
        self.download_via_egghead_downloader(tech_slug, course_title, course_url)

downloader = EggheadDownloader()
if args.slug:
    downloader.downloadSpecifiedCourse()
elif args.technology:
    downloader.downloadSpecifiedTechnology()
else:
    downloader.downloadAll()
