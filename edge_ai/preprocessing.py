import cv2

def preprocess_frame(image_input, target_size=(640, 640)):
    """
    Accepts an image file path (str) or raw image array (numpy matrix).
    Resizes it to standard YOLO target resolution.
    """
    if isinstance(image_input, str):
        frame = cv2.imread(image_input)
        if frame is None:
            raise FileNotFoundError(f"Could not load image at path: {image_input}")
    else:
        frame = image_input

    resized_frame = cv2.resize(frame, target_size)
    return frame, resized_frame