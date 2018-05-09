# [Egghead.io](https://egghead.io) Video Downloader

NOTE: To download premium videos, you're required to have an egghead.io premium account.


## REQUIREMENTS

- python 3.x
- [pipenv](https://pipenv.org)

### Install requirements
	pipenv install

## USAGE

**Step1:** Edit `config.py` and replace `your username here` and `your password here` with your own.

**Step2:** Edit `cookies.txt` and copy and paste academy.fm site's cookie.
To copy the cookie, I used [cookies.txt](https://chrome.google.com/webstore/detail/cookiestxt/njabckikapfpffapmjgojcnbfjonfjfg?hl=en), a chrome extension.

**Step3:** Excute the command below.

	python dl.py [OPTIONS]

## OPTIONS

	--mastercource		mastercource name (default: ableton)

	--slug			  course slug (default: None)
			  		  it'll be shown as its url.

	--directory		 directory where videos will be added
						e.g. ~/Desktop/academyfm

## EXAMPLES

Download all courses in academy.fm

	python dl.py

Download a specific course

	python dl.py --slug getting-started-with-react

Download all courses in a specific technology and put them to `~/Desktop/videos/ableton/*`

	python dl.py --mastercourse ableton --directory ~/Desktop

## OUTPUT

Downloaded videos will be stored in
 `./videos/TECHNOLOGY_NAME/COURSE_NAME/INDEX-LESSON_NAME.[ext]`

e.g. `./videos/ableton/ableton-live-10-essential-training/01-Intro&Highlights.mp4`
