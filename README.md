# sqm-in-a-box
Sky Quality Meter Recording Station with GPS, and QHYCCD

Python scripts to run a SQM station with GPS and QHYCCD.

Setup Steps

1. Install pip
    Linux with apt/apt-get: sudo apt-get install python-pip

2. Run the following commands to install the required Python packages.
    sudo apt-get install python-distutils
    sudo pip install pytx pytz datetime tzlocal skyfield python-crontab python-dateutil

3. Create the logs path
    mkdir -p ~/sqm-in-a-box/logs/

4. Copy the example_config.ini file to config.ini and update it with your station information

    
