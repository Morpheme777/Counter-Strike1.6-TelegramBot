from csdata import CSStats
import json
import datetime
import os
from ftplib import FTP
from struct import *

WORK_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_FOLDER = WORK_DIR + "/data"
LOGS_FOLDER = WORK_DIR + "/logs"


def downloadLogs():
    ftp = FTP(host='83.222.115.202')
    ftp.login(user='gs7336', passwd='UoN8pudmG')  # already expired
    ftp.cwd('addons/amxmodx/logs/')

    filenames = ftp.nlst() # get filenames within the directory

    for filename in filenames:
        local_filename = os.path.join('{}/'.format(LOGS_FOLDER), filename)
        file = open(local_filename, 'wb')
        ftp.retrbinary('RETR '+ filename, file.write)

        file.close()

    ftp.quit()

def main():
    downloadLogs()
    if not os.path.exists(DATA_FOLDER):
        os.mkdir(DATA_FOLDER)

    csstats = CSStats()
    datastamp = datetime.datetime.strftime(datetime.datetime.now(),"%Y%m%d")
    print(datastamp)
    csdata_file = '{}/csdata_{}.dat'.format(DATA_FOLDER,datastamp)
    csstats.downloadFile(csdata_file)
    csstats.decodeFile(csdata_file)
    players_stat = csstats.players_stat
    csdata_file_json = '{}/csdata_{}.json'.format(DATA_FOLDER,datastamp)
    f = open(csdata_file_json, "w")
    f.write(json.dumps(players_stat))
    f.close

if __name__ == '__main__':
    main()
    
