from csdata import CSStats
import json
import datetime
import os

WORK_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_FOLDER = WORK_DIR + "/data"

def main():

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
    
