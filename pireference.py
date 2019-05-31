from __future__ import division
import cv2
import numpy as np
import sys
import picamera

from UDPComms import Publisher

from fetch import find_ball_direct

capture_res = (1600, 1200)

iso_step = 50
ISO_MIN = 50
ISO_MAX = 800


def main(argv):

    shutter = int(argv[0])
    iso = 400

    cam_params = {"shutter" : shutter}
    cam_params = {"iso" : iso}

    reference = Publisher(9010)

    camera = picamera.PiCamera(sensor_mode=2, resolution=capture_res, framerate=10)
    camera.shutter_speed = shutter
    camera.iso = iso
    

    while True:
        image = np.empty((capture_res[1] * capture_res[0] * 3), dtype=np.uint8)
        camera.capture(image, 'bgr')
        image = image.reshape((capture_res[1], capture_res[0], 3))
        img_h, img_w = image.shape[0:2]

        truth = image[ 
            int(img_h * 0):int(img_h * 0.3), 
            int(img_w * 0):int(img_w * 0.3), 
        :]   
        truth_hsv = cv2.cvtColor(truth, cv2.COLOR_BGR2HSV)

        fname = "truth.jpg"
        cv2.imwrite(fname, truth)

        brightpoint = np.percentile(truth_hsv[:, :, 2], 95)
        toobright = brightpoint > 180
        toodark = brightpoint < 80

        if(toodark or toobright):
            if toobright:
                iso -= iso_step

            if toodark:
                iso += iso_step

            iso = max(ISO_MIN, min(iso, ISO_MAX))
            camera.iso = iso

            print("ISO changed: %d" % (iso))
            continue

        # exposure is ok, let's send over reference colors
        cam_params["range_hue"] = np.percentile(truth_hsv[:, :, 0], (5, 95)).tolist()
        cam_params["range_sat"] = np.percentile(truth_hsv[:, :, 1], (5, 95)).tolist()
        cam_params["range_val"] = np.percentile(truth_hsv[:, :, 2], (5, 95)).tolist()
        cam_params["iso"] = iso
        reference.send(cam_params)


        print(cam_params)



if __name__ == '__main__':
    if(len(sys.argv) > 2):
        print("Usage: pireference <shutter time ms>")
    main(sys.argv[1:])
    camera.close()