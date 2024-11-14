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
4. Take the SD card out of the Teensy from inside the yellow box of the FloatyBoat and copy the file `logs/pose.csv` to your own directory. 