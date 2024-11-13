#!/usr/bin/env python3

# Using all pose data from ASV to write a separate csv file with each GoPro image name and the interpolated GPS coord
#
#
# Written by: Serena Mou
# Date: 16/03/2022, updated: 13/11/24
from csv import writer
from PIL import Image
import glob
import numpy as np
import pandas as pd
import os
from datetime import datetime,timezone,timedelta
import re
import argparse
import sys


class interpolate_GP():
    def __init__(self, im_root, save_path, pose, date, thresh, tz):


        # Location to save csv
        self.save_path = save_path
        if not os.path.isfile(self.save_path):
            with open(self.save_path, 'a') as f:
                header = ["NAME", "LAT", "LON", "HEIGHT"]
                writer_obj = writer(f)
                writer_obj.writerow(header)
                f.close()
        else:
            x = input("csv file %s already exists. Add to file? Y/N "%self.save_path)
            if x.lower() != "y":
                sys.exit("Exiting...")
        # Location of csv file
        csv_path = pose

        # Location of folder of images to add exif to
        #img_folders = root_folder+'/**/*.JPG'
        self.imgs = glob.glob(os.path.join(im_root,'**/*.JPG'))
        date = date.split(',')
        #img_path = '/media/serena/PortableSSD/plot10/'

        # Deployment date of images to add exif to (year,month,day)
        self.deploy_date = datetime(int(date[0]), int(date[1]), int(date[2]))
        #input()

        # Timezone in GMT (of GoPro)
        self.timezone = tz
        self.thresh = thresh

        # Load csv
        data = pd.read_csv(csv_path, header=None, dtype=str)
        data.columns=["NMEA","VEH","DATE","TIME","LON","LAT","VEL","MPS","HEAD","D","DEPTH","M","BATT","V","X1","X2","MISSION","CS"]
        # csv format
        # <message_type><asv_id><date><time><long><lat><speed><heading><depth><volts><error_mode><control_mode><mission_name><waypoint_num>

        self.date = data.loc[:,"DATE"] #XDMMYY
        self.time = data.loc[:,"TIME"] #XHHMMSS.S in GMT
        self.lon  = data.loc[:,"LON"] #Decimal Degrees
        self.lat  = data.loc[:,"LAT"] #Decimal Degrees

        


    # convert pose csv time and date (GMT+0) to local time (GoPro time)
    # input csv time(str) and date(str), output datetime(datetime)
    def time_cvt(self, time_GMT, date):
        #print("raw time, raw date", time_GMT,date)

        # check date is valid
        if date == '0' or len(date)<5 or date == None:
            return datetime(1,1,1)

        msec = int(0)
        split_time = time_GMT.split('.')
        # get milliseconds
        if len(split_time)>1:
            msec =int(float('0.'+split_time[1])*1000000)
        

        # pad time not including ms
        time = split_time[0].zfill(6)
        sec = int(time[-2:])
        minute = int(time[2:4])
        hour = int(time[:2])
        #print(hour, minute, sec)

        # if the time is not valid
        if sec > 59 or minute > 59 or hour == "":
            return datetime(1,1,1) 
        

        year = int('20'+date[-2:])
        month = int(date[-4:-2:])
        if month < 1 or month > 12:
            return datetime(1,1,1)
        day = int(date[:-4:])

        csv_time = datetime(year,month,day,hour,minute,sec,msec)
        local_time = csv_time+timedelta(hours=self.timezone)
        #print("converted date time", local_time.strftime('%F %T.%f'))
        #input()

        return local_time


    # convert to datetime format, cull to only data from date of deployment
    # output qld_datetime(datetime list), lon(float64 list), lat(float64 list)
    def cvt_cull_all(self, dates,time,lon,lat,deploy_date):
        day_datetime = []
        day_lon = []
        day_lat = []
        for i,date in enumerate(dates):
    #         print(time_cvt(time[i],date).date(),deploy_date.date())
            if self.time_cvt(time[i],date).date() == deploy_date.date():
                day_datetime.append(self.time_cvt(time[i],date))
                day_lon.append(lon[i])
                day_lat.append(lat[i])

        #full_datetime = [time_cvt(time[i],date[i]) for i in range(len(date)) if time_cvt(time[i],date[i]).date() == deploy_date.date()]
        return day_datetime,day_lon,day_lat

    # Interpolate the GPS location from the time differences of the GoPro image taken and closest times in the ASV pose csv
    def interpolate(self,high,low,gpsh, gpsl):
        # High is the time/gps coord (lat OR lon) on pose.csv just after the image timestamp
        # Low is the time/gps coord (lat OR lon) on pose.csv just before the image timestamp
        # Return the interpolated GPS coordinate
        # print('function in',high,low,gpsh,gpsl)

        dt = np.float64(high)- np.float64(low)
        if dt == 0:
            return np.float64(gpsh)
        dgps = np.float64(gpsh)-np.float64(gpsl)
        diff = dgps * (np.float64(abs(low))/dt)
        return np.float64(gpsl) + diff

    def run(self):
        # cull the list of coordinates to just the ones from the deploy date
        day_list, day_lon, day_lat = self.cvt_cull_all(self.date,self.time,self.lon,self.lat,self.deploy_date)

        # for each image in a folder of images
        out_thresh = 0
        for image_path in sorted(self.imgs):
            #with open(image_path, 'rb') as image_file:
            #    image_bytes = image_file.read()
            # load image
            image = Image.open(image_path)
            img_exif= image.getexif()

            if img_exif is None:
                print("no exif found for "+image_path)

            else:
                val = [v for k,v in img_exif.items() if k == 306]
                photo_ref = image_path.split('/')[-1]
                #print(photo_ref)
                #print(val)
                # get time on image
                s = re.split(' |:',str(val[0]))
                img_time = datetime(int(s[0]),int(s[1]),int(s[2]),int(s[3]),int(s[4]),int(s[5]))
                diff_list = []
                min_p = 1000 # the smallest positive 
                min_n = -1000 # the smallest negative
                
                for i,dt in enumerate(day_list):
                    diff = datetime.timestamp(img_time)-datetime.timestamp(dt)
                    if diff > 0 and diff < min_p:
                        ind_pp = i
                        min_p = diff
                    elif diff < 0 and diff > min_n:
                        ind_nn = i
                        min_n = diff
                    elif diff == 0:
                        ind_pp = i
                        ind_nn = i
                        min_p = diff
                        min_n = diff
                    #diff_list.append(datetime.timestamp(img_time)-datetime.timestamp(dt))

            # Check this thresh value
            if abs(min_p) < self.thresh and abs(min_n) < self.thresh:
                img_lon = self.interpolate(min_p,min_n,day_lon[ind_pp],day_lon[ind_nn])
                img_lat = self.interpolate(min_p,min_n,day_lat[ind_pp],day_lat[ind_nn])
                
                write_line = (photo_ref ,str(img_lat),str(img_lon),0)
                with open(self.save_path, 'a') as f:
                    writer_obj = writer(f)
                    writer_obj.writerow(write_line)
                    f.close()
            
            else:
                #print(img_time, day_list[ind_pp], day_list[ind_nn], ind_pp, ind_nn)
                print("image %s has no values within threshold. min_p = %f, min_n = %f"%(image_path, min_p, min_n))
                out_thresh += 1
                #input()
        print("%i/%i images outside threshold"%(out_thresh,len(self.imgs)))
    
        return


def arg_parse():
    parser = argparse.ArgumentParser(description="Use pose data from FloatyBoat and write csv matching GoPro name and interpolated GPS coords")
    
    parser.add_argument("-r", "--root", dest = "root",
            help = "Path to root folder with all files in standard format. If not in standard format, use other args.", default = None, type = str, required=False)

    parser.add_argument("-ir", "--im_root", dest = "im_root",
            help = "Path to GoPro root folder. Required if --root not set.", default = None, type = str, required=False)

    parser.add_argument("-s", "--save_path", dest = "save_path",
            help = "Path (including name) of csv file to save results. Required if --root not set.", default = None, type = str, required=False)

    parser.add_argument("-p", "--pose", dest = "pose",
            help = "Path to pose.csv from FloatyBoat. Required if --root not set.", default = None, type = str, required=False)

    parser.add_argument("-d", "--date", dest = "date",
            help = "Date of deployment speed up filtering of GPS info. In format YYYY,MM,DD.", default = None, type = str, required=True)
    
    parser.add_argument("-t", "--thresh", dest = "thresh",
            help = "(Optional) threshold for filtering in seconds. Default is 1 second.", default = 1, type = float, required=False)
    
    parser.add_argument("-tz", "--timezone", dest = "tz",
            help = "(Optional) timezone in GMT. Default is 10.", default = 10, type = int, required=False)
     
    return parser.parse_args()


def main():
    args = arg_parse()
    if args.root:
        im_root = os.path.join(args.root,"images")
        save_path = os.path.join(args.root,"output.csv")
        pose = os.path.join(args.root,"pose.csv")
    else:
        im_root = args.im_root
        save_path = args.save_path
        pose = args.pose
    
    interp = interpolate_GP(im_root, save_path, pose, args.date, args.thresh, args.tz)
    interp.run()

    print("DONE")

if __name__=="__main__":
    main()