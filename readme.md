#Refurence
=========================
http://refurence.net - a website for furry character references 


##Setup

###Prerequisites


1. [Python 2.7](https://www.python.org/) with [pip](https://pip.pypa.io/en/latest/installing.html) 
... Using the python3 will prevent the code from running. You can tell which version you're using with `python -V`

2. [VirtualEnv](http://docs.python-guide.org/en/latest/dev/virtualenvs/) and [VirtualEnvWrapper](http://virtualenvwrapper.readthedocs.org/en/latest/install.html) 

3. [MongoDB](http://www.mongodb.org/)
... You'll need to set up a database with an admin user for the app to connect to.


###Installation


1. Download via git:

        git clone https://github.com/dbdeadbeat/refurence.git

2. Change into the cloned directory

        cd refurence

3. Create a virtualenvironment

        mkvirtualenv environment

4. Install the required python dependencies:

        pip install -r requirements.txt

5. Enter config info in `flask_application/config.py`

6. Set up database

        python manage.py populate_db
        python manage.py populate_data
    
7. Run a development server:
        
        python manage.py runserver


Assuming everything went smoothly, you should now be live on [http://localhost:5000/]

##Usage

###Commands
_Run these commands by using `python manage.py <command>`_


* `reset_db` - Drops all Mongo documents
* `populate_db` - Script to fill the database with new data (either for testing or for initial). You can edit the `populate_data` command in `flask_application/script.py` (Right now it is set up to add Users.)
* `runserver` - Runs a debug server
* `clean` - Removes *.pyc files
* `shell` - Opens a shell within the Flask context
* `show_urls` - Lists the urls that are available
* `run_tests` - Runs unittests using nose.
* Commands included with Flask-Security can be found here: http://packages.python.org/Flask-Security/#flask-script-commands and by looking in `flask_application/script.py`

###Templates
All html templates are stored here in './templates'

###Running Tests
You can run the unittests either with `ENVIRONMENT=TESTING ./manage.py run_tests`, with `ENVIRONMENT=TESTING . /bin/run_tests.sh` or `ENVIRONMENT=TESTING nosetests`.

###Static Content
All static content is stored here in './static'


##TODO List
-----------
* Mobile profile editing
* Better copy/paste in editing (parse out style/paste only plaintext)
* Admin portion of site(?) - not sure if worth the effort
* Better utilites for using images hosted on FA
* Better testing
* Add a contact info portion to site
* Whatever is cool; do something cool
* Have a bunch of fun :33333


##Credit
------
###Required Python Projects:

* unittest2
* Flask
* Flask-Assets
* cssmin
* Flask-WTF
* Flask-Script
* Flask-Mail
* Flask-Cache
* Flask-Security
* Flask-MongoEngine
* Flask-Testing
* python-memcached

###Non-Python Projects:
* Twitter Bootstrap

###Contributing Projects:
* Flask-Security
* https://github.com/mbr/flask-bootstrap

LICENSE &amp; COPYRIGHT
-----------------------
The MIT License

Copyright (c) 2015 deadbeat <edeadbeat@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
