from datetime import datetime
import json
import os


class timeTracking():
    def __init__(self):
        super().__init__()

    def start_time(self, fileName, key_name, recordtime=None):
        json_time_object = {key_name : recordtime}
        timeToJson = json.dumps(json_time_object, default=str)
        with open(fileName, 'w') as out2file:
            out2file.write(timeToJson)


    def read_last_record_time(self, fileName, key_name):
        with open(fileName, 'r') as openfile:
            record_file = json.load(openfile)
        last_time = datetime.fromisoformat(record_file[key_name])
        return last_time 


    def filter_data_follow_CT(self, datalist: list, dataCTlist: list, key_name: str, now):
        print("[INFO] Filter data from Create Time...")
        filtered_data_list = []
        if key_name=='Bonding':
            if not os.path.exists('Run_Bond_TimingRecord.json'):
                self.start_time('Run_Bond_TimingRecord.json', key_name, recordtime=now)
                initial_time = now.replace(year=2022, month=10, day=1, hour=0, minute=0, second=0)
                for file, filetime in zip(datalist, dataCTlist):
                    if filetime < now and filetime > initial_time:
                        filtered_data_list.append(file)
                return filtered_data_list
            else:
                last_time = self.read_last_record_time('Run_Bond_TimingRecord.json', key_name)
                self.start_time('Run_Bond_TimingRecord.json', key_name, recordtime=now)
                for file, filetime in zip(datalist, dataCTlist):
                    if filetime < now and filetime > last_time:
                        filtered_data_list.append(file)
                return filtered_data_list

        if key_name=='AOI':
            if not os.path.exists('Run_AOI_TimingRecord.json'):
                self.start_time('Run_AOI_TimingRecord.json', key_name, recordtime=now)
                initial_time = now.replace(year=2022, month=10, day=1, hour=0, minute=0, second=0)
                for file, filetime in zip(datalist, dataCTlist):
                    if filetime < now and filetime > initial_time:
                        filtered_data_list.append(file)
                return filtered_data_list
            else:
                last_time = self.read_last_record_time('Run_AOI_TimingRecord.json', key_name)
                self.start_time('Run_AOI_TimingRecord.json', key_name, recordtime=now)
                for file, filetime in zip(datalist, dataCTlist):
                    if filetime < now and filetime > last_time:
                        filtered_data_list.append(file)
                return filtered_data_list

      
