#!/usr/bin/python
"""
================================================================
Get updates script.
----------------------------------------------------------------
Check if updates.txt exists on darkskynz.org for this device_id
if it does;
config.ini -Retieve the config.ini settings and update both copies of config.ini. Upon successful completion use api.php to remove update file.
git pull - If triggered will either be immediate and run directly from script or scheduled and run from sunset or sunrise scripts
"""
import os, shutil

basepath = os.path.expanduser('~/sqm-in-a-box/')

configfile = '/tmp/config.ini'
if not os.path.exists(configfile):
	if os.path.exists(basepath + 'config.ini'):
		shutil.copy(basepath + 'config.ini', '/tmp/')

logpath = basepath + 'logs/'
if not os.path.isdir(logpath):
	os.makedirs(logpath)

datapath = basepath + 'data/'
if not os.path.isdir(datapath):
	os.makedirs(datapath)
	
sqm_logfile = basepath +'logs/sqm.log'

import configparser, sys
from distutils.util import strtobool

config = configparser.ConfigParser()
config.read(configfile)

debug = config["debug"]
debugmode = config.get('debug', 'debugmode')

import logging
# set up logging to file
if debugmode == 'debug':
	logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
					datefmt='%Y-%m-%d %H:%M',
					filename=sqm_logfile)
	# define a Handler which writes DEBUG messages or higher to the sys.stderr
	console = logging.StreamHandler()
	console.setLevel(logging.DEBUG)
else:
	logging.basicConfig(level=logging.INFO,
					format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
					datefmt='%Y-%m-%d %H:%M',
					filename=sqm_logfile)
	# define a Handler which writes INFO messages or higher to the sys.stderr
	console = logging.StreamHandler()
	console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)

logger = logging.getLogger('updates')

logger.debug('basepath: ' + basepath)
logger.debug('logpath: ' + logpath)

import getpass
current_user = getpass.getuser()

logger.debug('current_user: ' + current_user)

try:
    gps = config["gps"]
    timezone = config.get('gps', 'timezone')
    latitude = config.getfloat('gps', 'latitude')
    longitude = config.getfloat('gps', 'longitude')
    elevation = config.getfloat('gps', 'elevation')
    location_description = config.get('gps', 'location_description')

    station = config["station"]
    apikey = config.get('station', 'apikey')
    station_id = config.get('station', 'station_id')
    has_internet = strtobool(config.get('station', 'has_internet'))
    is_mobile = strtobool(config.get('station', 'is_mobile'))
    has_gps = strtobool(config.get('station', 'has_gps'))
    station_name = config.get('station', 'name')
    configured = config.get('station', 'configured')
    is_configured = strtobool(configured)

    sqm = config["sqm"]
    sqm_type = config.get('sqm', 'type')
    instrument_id = config.get('sqm', 'instrument_id')

    mail = config["mail"]
    smtp_server = config.get('mail', 'smtp_server')
    smtp_port = int(config.get('mail', 'smtp_port'))
    mailbox_username = config.get('mail', 'mailbox_username')
    mailbox_password = config.get('mail', 'mailbox_password')
    frequency = config.get('mail', 'frequency')

    logger.debug('Read values from config.ini')
except KeyError as e:
	logger.warn("Error reading the configuration section {}".format(e))
	logger.debug('Failed to read values from config.ini')

logger.debug('Config file')

for each_section in config.sections():
    logger.debug('Section: ' + each_section)
    for (each_key, each_val) in config.items(each_section):
        logger.debug(each_key + ' : ' + each_val)

import getpass
current_user = getpass.getuser()

from crontab import CronTab
my_cron = CronTab(user=current_user)

#    my_cron.env['MAILTO'] = 'justin@darkskynz.org'
exists_update_git = exists_get_updates = False

for job in my_cron:
    if "git pull code updates" in str(job):
        exists_update_git = True
    if "Get updates" in str(job):
        exists_get_updates = True

if apikey != "":
    import datetime
    from datetime import datetime
    import pytz, tzlocal

    tz = pytz.timezone(timezone)
    now = datetime.now(tz)

    import requests
    updatefile = '/tmp/update.txt'
    url = 'https://darkskynz.org/sqminabox/' + apikey + "/update.txt"
    logger.debug('Request URL: ' + url)
    myfile = requests.get(url, headers={'User-Agent': 'Unihedron SQM-LE and Raspberry Pi'})
    
    if myfile.status_code == 200:
        open(updatefile, 'wb').write(myfile.content)
        logger.debug('Update file')

        update = configparser.ConfigParser()
        update.read(updatefile)

        updatelog = open('/tmp/update.log', "w+")
        something_changed = False

        for each_section in update.sections():
            logger.debug('Section: ' + each_section)
            for (each_key, each_val) in update.items(each_section):
                try:
                    old_value = config.get(each_section, each_key)
                except:
                    old_value = ''
                logger.debug('Key: ' + each_key + ' : ' + old_value + ' : ' + each_val)
                if old_value != each_val:
                    something_changed = True
                    config.set(each_section, each_key, str(each_val))
                    str_updated_value = str(now.isoformat()) + ' : ' + str(each_section) + ' : ' + str(each_key) + ' : ' + str(old_value) + ' ; ' + str(each_val) + '\n'
                    updatelog.write(str_updated_value)

        if something_changed == False:
            updatelog.write('Nothing changed!')

        # Writing our configuration file to 'config.ini'
        with open(configfile, 'wb') as thisconfigfile:
            config.write(thisconfigfile)
            thisconfigfile.close()
            shutil.copy(configfile, basepath + 'config.ini')

        try:
            git_pull = config.get('station', 'update_code')
        except:
            git_pull = 'False'

        if exists_update_git == True:
            for job in my_cron.find_comment('git pull code updates'):
                if git_pull == 'urgent':
                    job.clear()
                    job.minute.every(15)
                    job.enable(has_internet)
                elif git_pull == 'scheduled':
                    job.clear()
                    job.hour.on(12)
                    job.minute.on(0)
                    job.enable(has_internet)
                else:
                    job.enable(False)
            my_cron.write()
            logger.debug('job: ' +str(job))
            logger.debug('git pull cron job modified successfully')
        elif exists_update_git == False:
            update_git_cron = my_cron.new(command='cd /home/' + current_user + '/sqm-in-a-box/ && git pull && https://darkskynz.org/sqminabox/api.php?action=update_processed&apikey=' + apikey, comment="git pull code updates")
            update_git_cron.hour.on(12)
            update_git_cron.minute.on(0)
            update_git_cron.enable(has_internet)
            my_cron.write()
            logger.debug('git pull code updates cron job created successfully')

        import requests

        params = (
            ('action', 'update_processed'),
            ('apikey', apikey),
        )

        response = requests.get('https://darkskynz.org/sqminabox/api.php', params=params, headers={'User-Agent': 'Unihedron SQM/LE and Raspberry Pi'})

        logger.debug('response.status_code: ' + str(response.status_code))
        logger.debug('response.content: ' + str(response.content))

        #if response.status_code == 200:

        updatelog.close()

if exists_get_updates == True:
    for job in my_cron.find_comment('Get updates'):
        job.clear()
        job.minute.on(0)
        job.enable(has_internet)
        logger.debug('job: ' + str(job))
        logger.debug('Get updates job modified successfully')
elif exists_get_updates == False:
    get_updates = my_cron.new(command='python /home/' + current_user + '/sqm-in-a-box/get_updates.py', comment="Get updates")
    get_updates.minute.on(0)
    get_updates.enable(has_internet)
    logger.debug('Get update cron job created successfully')
