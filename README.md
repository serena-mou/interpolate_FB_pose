# interpolate_FB_pose
Interpolate the pose from FloatyBoat GPS and match to timestamps on GoPro images for use in photogrammetry. 

---
## 0. Collecting data

1. Set up GoPro
    - ***!!! This is very important: !!! Sync the GoPro via the Quik app to a phone that has the date and time set automatically.***
    - Your specific settings may vary due to your particular flavour of GoPro, but in general, set the GoPro to collect a *TimeLapse* with the settings: 
        - Lens: Linear
        - Format: Photo
        - Interval: 0.5s
        - Output: Standard
        - Duration: No Limit
        - Timer: Off 
2. Start GoPro around the same time as starting the mission from the FloatyBoat. The GPS coordinates are not being stored on the FloatyBoat if there is no mission running. 
3. Copy the GoPro images off the SD card in the GoPro. Save them to your own directory, keeping the GoPro default file structure. eg. `100GOPRO, 101GOPRO ... 110GOPRO`
4. Take the SD card out of the Teensy from inside the yellow box of the FloatyBoat (see image below) and copy the file `logs/pose.csv` to your own directory. 

![alt text](https://github.com/serena-mou/interpolate_FB_pose/blob/0925f2ec8958fb3fa338fdefab738ebed124b03f/examples/FB_SD.jpg?raw=true "SD Card")

5. Ideally, organise your data into the following format. The code will still work if organised differently. 

```
└── "root_folder"/
    ├── images/
        ├── 100GOPRO/
            ├── G0011999.JPG
            ├── G0012000.JPG
            ├── ...
            └── G0012997.JPG
        └── 101GOPRO/
            ├── G0012998.JPG
            ├── G0012999.JPG
            ├── ...
            └── G0013997.JPG
    └── pose.csv
       
```

---
## 1. Interpolating

Running the script WITH a standard format root folder:

**Example usage:**
```
python3 interpolate_gopro.py --root /path/to/root_folder --date 2024,09,24 --thresh 4 
```

Running the script withOUT a standard format root folder:

**Example usage:**
```
python3 interpolate_gopro.py --im_root /path/to/folder/of/GoPro/folders --save /path/to/save/output.csv --pose /path/to/pose.csv --date 2024,09,24 --thresh 4 
```


**Options:**
- `--root str` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Path to root folder with all files in standard format, expects `/root_folder/images`, `/root_folder/pose.csv`.
- `--im_root str` &nbsp;  Required if `--root` not set. Path to GoPro root folder. 
- `--save str` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Required if `--root` not set. Path (including name) of csv file to save results. 
- `--pose str` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Required if `--root` not set. Path to pose.csv from FloatyBoat. 
- `--date str` &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Date of deployment speed up filtering of GPS info. In format YYYY,MM,DD.
- `--thresh float`  (Optional) threshold for filtering in seconds. Default is 1 second. **See Note 1.**
- `--timezone int`  (Optional) timezone in GMT that the GoPro images are in. Default is 10. (QLD is GMT+10).


**Output:**
- `path/to/root_folder/output.csv` csv file containing IMG_NAME, LAT, LON, HEIGHT on each line, for each image


### *Note 1:*
To interpolate, we find the two GPS coordinates from `pose.csv` that closest match the time on the GoPro image (read from the exif data on the image). We calculate a `min_p` which is the smallest positive time difference between the image time and a recorded GPS time, as well as a `min_n` which is the smallest negative time difference. We compare `min_p` AND `min_n` to `thresh` and as such, the two GPS points being interpolated may be up to 2*`thresh` apart. For example, if you set `thresh` to 4 seconds, `min_p` may be 4 seconds and `min_n` may be -4 seconds, meaning the two closest GPS points are 8 seconds apart. Keep this in mind. 