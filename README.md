# sqm-in-a-box
Sky Quality Meter Recording Station with GPS, and QHYCCD

Python scripts to run a SQM station with GPS and QHYCCD.

Setup Steps

1. Install pip
    Linux with apt/apt-get: sudo apt-get install python-pip

2. Run the following commands to install the required Python packages and the git client.

    sudo apt-get update
    sudo apt-get upgrade
    sudo apt-get install python-dev python-distutils-extra python-pip python-numpy git dnsutils ssmtp mailutils
    sudo pip install pytx pytz datetime tzlocal 
    sudo pip install skyfield 
    sudo pip install python-crontab 
    sudo pip install python-dateutil 
    sudo pip install requests

3. Download the SQM-in-a-Box scripts from the git repository.
    These will run under a standard user, say the default Raspberry Pi user pi, so can be installed from the home directory.
    
    git clone https://github.com/KiwiMorpheus/sqm-in-a-box.git

3. Copy the example_config.ini file to config.ini and update it with your station information
    Update the following settings
        gps Section
            Set the known latitiude, longitude, elevation.
            Update the description with the Street Name and Suburb of the station location.
            Set the timezone using the standard tz database name format as found here https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
        station Section
            Set the is_mobile and has_gps parameters if this is a mobile station with a GPS unit attacted to it.
        sqm Section
            Set the instrument-id. In most cases you will be given this.
            Set the connection to either eth or usb depednign on SQM connection type. The code will detect the sqm_addresss or usp_port parameters.
            If you have changed the SQM tcp_port then update the default 10001 to the new setting.
        mail Section
            If you have your own mail server or wish to use your own email account update these settings.
            If you wish to receieve the SQM data then add your email address to the recipient line placing a comma between the email address(es)
            If the smtp_server setting is left at the default settings the first time the startup.py is run it will update these settings.

4. Run SQM-in-a-Box startup.py script to configure your station.
    cd sqm-in-a-box
    python startup.py

    This will setup your station depending on the config.ini settings from step 3.
    Task cron jobs will be setup and configured as follows(These do not rquire root access)
        Query SQM - This task queries the SQM Meter every minute from sunset to sunrise, except if mobile then every 5 minutes.
        Start up cron - This will run on startup and will attempt ot detect the SQM Meter and update the configuration if anything changes.
        Sunset crons - Switches on the Query SQM cron job and creates the datafile for the nights readings. If is a mobile station with GPS it will fire up the Read GPS cron job as well. This will adjust the Send Data freequency depending on the mail frequency set.
        Sunrise crons - These will switch off the Query SQM cron job. 
        Send Data - Will send the data at 9am either daily or for weekly on the Monday or monthly on the first day of the month.
