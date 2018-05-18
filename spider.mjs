#!/usr/bin/env node

require('dotenv').config();
const fs = require('fs-extra');
const puppeteer = require('puppeteer');
const ArgumentParser = require('argparse').ArgumentParser;
const { exec } = require('child_process');

const parser = new ArgumentParser({
  version: '0.0.1',
  addHelp: true,
  description: 'A tiny script for downloading videos on academy.fm',
});

class Spider {
  constructor() {
    this.args = this._parseArgs();
    this.baseUrl = 'https://academy.fm';
    this.baseCategoryUrl = `${this.baseUrl}/courses-tutorials`;
    this.coursesUrl = `${this.baseUrl}/courses`;
    this.tutorialsUrl = `${this.baseUrl}/tutorials`;
    this.loginPageUrl = `${this.baseUrl}/signin/`;

    // bind this to all functions
    this._parseArgs = this._parseArgs.bind(this);
    this._getContent = this._getContent.bind(this);
    this._getAllCategorySlugs = this._getAllCategorySlugs.bind(this);
    this._getACourse = this._getACourse.bind(this);
    this._getLessonUrls = this._getLessonUrls.bind(this);
    this._getDirectoryName = this._getDirectoryName.bind(this);
    this._showCourseTitle = this._showCourseTitle.bind(this);
    this._downloader = this._downloader.bind(this);
    this._downloadVideos = this._downloadVideos.bind(this);
    this._downloadAll = this._downloadAll.bind(this);
    this._downloadSpecifiedCategory = this._downloadSpecifiedCategory.bind(this);
    this._downloadSpecifiedCourse = this._downloadSpecifiedCourse.bind(this);
    this.page = null;
  }

  _parseArgs() {
    parser.addArgument(
      ['-c', '--category'],
      {
        help: 'specify a category (default: ableton)',
      }
    );

    parser.addArgument(
      ['--course'],
      {
        help: 'download videos in a course with this flag and --slug or -s flag',
        defaultValue: true,
        action: 'storeTrue',
      }
    );

    parser.addArgument(
      ['--tutorial'],
      {
        help: 'download videos in a tutorial with this flag and --slug or -s flag',
        action: 'storeTrue',
      }
    );

    parser.addArgument(
      ['-s', '--slug'],
      {
        help: 'specify a course slug to download a course with the specified slug',
      }
    );

    parser.addArgument(
      ['-o', '--output'],
      {
        help: 'specify a output directory where downloaded videos will be added (default: ./videos)',
        defaultValue: './videos',
      }
    );

    return parser.parseArgs();
  }

  async _isLoggedIn() {
    return await this.page.evaluate(()=> {
      const node = document.querySelectorAll('.login-btn');
      return node.length ? false : true;
    });
  }

  async _login(url) {
    // if not logged in, then login
    const isLoggedIn = await this._isLoggedIn();
    console.log('is logged in? ', isLoggedIn);
    if(!isLoggedIn) {
      console.log('goto the login page');
      await this.page.goto(this.loginPageUrl, { timeout: 0 });

      // if no USERNAME and PASSWORD specified in .env, then thrown an error.
      const { USERNAME, PASSWORD } = process.env;
      if(!(USERNAME && PASSWORD && USERNAME.length && PASSWORD.length)) {
        new Error('Please fill out in .env USERNAME and PASSWORD with yours')
      }

      // type USERNAME and PASSWORD
      await this.page.type('input[name="log"]', USERNAME);
      await this.page.type('input[name="pwd"]', PASSWORD);

      // click submit button with the info above
      await this.page.click('#wp-submit');

      // then wait until navigation ends
      await this.page.waitForNavigation();

      console.log('Successfully logged in!');
      await this.page.goto(url, { timeout: 0, waitUntil: 'domcontentloaded' });
    }

  }

  async _getContent(url) {
    console.log('get content', url);
    // first go to the url
    await this.page.goto(url, { timeout: 0, waitUntil: 'domcontentloaded' });
    await this._login(url);
    // get html
    const content = await this.page.$('body');
    return content;
  }

  async _getACategory(categorySlug) {
    console.log('get a category', categorySlug);
    const url = `${this.baseCategoryUrl}#category=${categorySlug}&level=all&instructor=all&type=all`;
    await this._getContent(url);
  }

  async _getAllCategorySlugs() {
    console.log('get all category slugs');
    const content = await this._getContent(this.baseCategoryUrl);
    const categorySlugs = await this.page.$$eval('.js-category-filter-item', items => items.map(item => item.getAttribute('data-category')));
    return categorySlugs;
  }

  async _getACourse(courseUrl) {
    console.log('get a course', courseUrl);
    const courseContent = await this._getContent(courseUrl);
    return courseContent;
  }

  async _getLessonUrls() {
    console.log('get lesson urls');
    const lessonUrls = await this.page.$$eval('.main-container iframe', lessons => lessons.map(lesson => lesson.getAttribute('src')));
    return lessonUrls;
  }

  _getDirectoryName(categorySlug, courseTitle) {
    console.log('get directory name');
    const directory = `${this.args.output}/${categorySlug}/${courseTitle}`;
    fs.ensureDirSync(directory);
    return directory;
  }

  _showCourseTitle(courseTitle) {
    console.log('-'.repeat(courseTitle.length))
    console.log(courseTitle);
    console.log('-'.repeat(courseTitle.length))
  }

  _downloader(categorySlug, courseTitle, lessonUrls) {
    console.log('downloader');
    const filePath = `${this._getDirectoryName(categorySlug, courseTitle)}/%(autonumber)s - %(title)s.%(ext)s`;

    // create youtube-dl command
    const youtubeDlCommand = `youtube-dl -v "${lessonUrls.join('" "')}" --referer "${this.baseUrl}" -o "${filePath}"`;
    console.log(youtubeDlCommand);

    // execute youtube-dl command
    exec(youtubeDlCommand, (err, stdout, stderr) => {
      if (err) new Error('node couldnt execute the command');

      // the *entire* stdout and stderr (buffered)
      console.log(`stdout: ${stdout}`);
      console.log(`stderr: ${stderr}`);
    });
  }

  async _downloadACourse(categorySlug, courseUrl, courseTitle) {
    await this._getACourse(courseUrl);
    const lessonUrls = await this._getLessonUrls();
    if(!courseTitle) {
      courseTitle = await this.page.$eval('.tutorial-title h1', title => title.innerHTML);
    }
    this._showCourseTitle(courseTitle);
    this._downloader(categorySlug, courseTitle, lessonUrls);
  }

  async _downloadCoursesFromACategory(categorySlug) {
    await this._getACategory(categorySlug);
    const selector = 'div.hover-bg-near-white.js-filter-item.course-entry:not(.dn)';
    const courses = await this.page.$$eval(selector, courses => courses.map(course => {
      const url = course.querySelector('a').getAttribute('href');
      const title = course.querySelector('h4').innerText;
      return { url, title };
    }));

    for(const course of courses) {
      const { url, title } = course;
      await this._downloadACourse(categorySlug, url, title);
    }
  }

  async _getACategorySlugByVideoUrl(url) {
    await this._getContent(this.baseCategoryUrl);
    const selector = `.course-entry a[href="${url}/"]`;
    const categorySlug = await this.page.$eval(selector, title => title.getAttribute('data-category').split(' ')[0]);
    console.log('category', categorySlug);
    return categorySlug;
  }

  async _downloadSpecifiedCategory(categorySlug) {
    await this._downloadCoursesFromACategory(categorySlug);
  }

  async _downloadSpecifiedCourse(slug, isCourse = true) {
    console.log(`download a ${isCourse ? 'course' : 'tutorial'}: ${slug} `);
    const baseUrl = isCourse ? this.coursesUrl : this.tutorialsUrl;
    const url = `${baseUrl}/${slug}`;
    const categorySlug = await this._getACategorySlugByVideoUrl(url);
    await this._downloadACourse(categorySlug, url);
  }

  async _downloadAll() {
    console.log('download all');
    const categorySlugs = await this._getAllCategorySlugs();
    for(const categorySlug of categorySlugs) {
      await this._downloadCoursesFromACategory(categorySlug);
    }
  }

  async _downloadVideos() {
    console.log('download videos');
    const { slug, category, tutorial } = this.args;
    // if -s and --tutorial specified then download a tutorial
    if(slug && tutorial) await this._downloadSpecifiedCourse(slug, false);
    // if only -s or -s and --course are specified then download a course
    else if(slug) await this._downloadSpecifiedCourse(slug);
    // if only -c is specified then download all videos in a category
    else if(category) await this._downloadSpecifiedCategory(category);
    // if nothing is specified then download all videos
    else await this._downloadAll();
  }

  async init() {
    const browser = await puppeteer.launch({
      args: ['--disable-dev-shm-usage'],
    });
    this.page = await browser.newPage();
    await this._downloadVideos();
    await browser.close();
  }
}

const spider = new Spider();
spider.init();
