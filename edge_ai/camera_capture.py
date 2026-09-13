import cv2

class CameraStream:
    def __init__(self, source=0):
        """
        Initializes camera stream from webcam index (0) or video file path.
        """
        self.source = source
        self.cap = cv2.VideoCapture(source)

    def read_frame(self):
        """
        Reads next frame from video capture device.
        """
        if not self.cap.isOpened():
            print(f"[ERROR] Could not open camera source {self.source}")
            return False, None
            
        ret, frame = self.cap.read()
        return ret, frame

    def release(self):
        self.cap.release()