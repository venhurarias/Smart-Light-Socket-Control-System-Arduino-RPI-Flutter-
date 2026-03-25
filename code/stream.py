import cv2
import threading
import time
import serial
import pyrebase
from flask import Flask, Response

serial_port = '/dev/ttyUSB0'  # Update this to match the actual port your Arduino is connected to
baud_rate = 9600
ser = serial.Serial(serial_port, baud_rate, timeout=0.1)

firebaseConfig = {
  "apiKey": "AIzaSyAoHN8L7QeFo-T8yRejZcLLskNTg9imeoc",
  "authDomain": "class-eye.firebaseapp.com",
  "databaseURL": "https://class-eye-default-rtdb.asia-southeast1.firebasedatabase.app",
  "projectId": "class-eye",
  "storageBucket": "class-eye.appspot.com",
  "messagingSenderId": "527255327157",
  "appId": "1:527255327157:web:f5b20f5d4bf5b6636189fc",
  "measurementId": "G-M050SV20XY"
};

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

isLightOpen=False
isExtensionOpen=False
timerCnt=0
app = Flask(__name__)
    
frame_bytes=0

def process_camera(camera):
    global frame_bytes
    while True:
        ret, frame = camera.read()
        cv2.imshow('Camera Stream', frame)
        if not ret:
            break
        
        # Convert the frame to JPEG format
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])

        if not ret:
            break
            
        # Convert the frame to bytes
        frame_bytes = buffer.tobytes()

def stream_handler(message, device):
    global isLightOpen;
    global isExtensionOpen;
    if device == 0:
        isLightOpen = (message['data']==True)
    elif device == 1:
        isExtensionOpen = (message['data']==True)
    if not isLightOpen or not isExtensionOpen:
        ser.write("0".encode())
    elif isLightOpen or not isExtensionOpen:
        ser.write("1".encode())
    elif not isLightOpen or isExtensionOpen:
        ser.write("2".encode())
    elif isLightOpen or isExtensionOpen:
        ser.write("3".encode())
    
def firebaseListen():
    db.child("d").child("U2NwJEV4tzPR3BWFr4dG").stream(lambda message: stream_handler(message, 0))
    db.child("d").child("5amPL2XuBZhRARFWQvyc").stream(lambda message: stream_handler(message, 1))

def listenSerial():
    global isLightOpen;
    global isExtensionOpen;
    while True:
        # Read a line of data from the Arduino
        data = ser.readline().decode('utf-8').strip()
        
        # Print the received data
        if data=="l":
            isLightOpen = not isLightOpen
            db.child("d").update({"U2NwJEV4tzPR3BWFr4dG":isLightOpen})
        elif data=="e":
            isExtensionOpen = not isExtensionOpen
            db.child("d").update({"5amPL2XuBZhRARFWQvyc":isExtensionOpen})

def hog_detection(camera):
    global isLightOpen;
    global isExtensionOpen;
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    while True:
        if isLightOpen or isExtensionOpen:
            ret, frame = camera.read()
            
            if not ret:
                #print("No Detection")
                continue
            # HOG detection
            (humans, _) = hog.detectMultiScale(frame, winStride=(8, 8),
            padding=(8, 8), scale=1.2)
            #print('Human Detected:', len(humans))
            if len(humans)>0:
                timerCnt=0
            else:
                timerCnt += 1
                if timerCnt>60:
                    isLightOpen = False
                    isExtensionOpen = False
                    db.child("d").update({"5amPL2XuBZhRARFWQvyc":isExtensionOpen})
                    db.child("d").update({"U2NwJEV4tzPR3BWFr4dG":isLightOpen})
                    
        else:
            timerCnt=0
        time.sleep(5)
        
def generate_frame():
    global frame_bytes
    while True:
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':

    
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Error: Ccould not open camera.")
        exit()
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) 
    camera.set(cv2.CAP_PROP_FPS, 15) 
    camera_thread = threading.Thread(target=process_camera, args=(camera,))
    camera_thread.start()
    hog_thread = threading.Thread(target=hog_detection, args=(camera,))
    hog_thread.start()
    serial_thread = threading.Thread(target=listenSerial)
    serial_thread.start()
    firebase_thread = threading.Thread(target=firebaseListen)
    firebase_thread.start()
    
    app.run(host='0.0.0.0', port=8000, debug=False)
    ser.close()
    camera.release()
    hog_thread.join()
    camera_thread.join()
