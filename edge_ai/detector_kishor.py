import os
from ultralytics import YOLO
from huggingface_hub import hf_hub_download

class RoadHazardDetector:
    # Human-readable labels for RDD2022 dataset classes
    CLASS_MAPPING = {
        "D00": "Longitudinal Crack",
        "D10": "Transverse Crack",
        "D20": "Alligator Crack",
        "D40": "Pothole",
        "Repair": "Repaired Road",
        "Road Damage": "General Road Damage"
    }

    def __init__(self, repo_id="rezzzq/yolo12s-road-damage-rdd2022", filename="yolo12s_RDD2022_best.pt"):
        print(f"[INFO] Initializing Road Hazard Detector...")
        model_path = None

        # 1. Try downloading fine-tuned weights from Hugging Face
        try:
            print(f"[INFO] Fetching pre-trained weights from Hugging Face repo: {repo_id}")
            model_path = hf_hub_download(repo_id=repo_id, filename=filename)
            print(f"[SUCCESS] Downloaded weights to: {model_path}")
        except Exception as e:
            print(f"[WARNING] Could not download from Hugging Face ({e})")

        # 2. Check local fallback in edge_ai/model/best.pt
        if not model_path or not os.path.exists(model_path):
            local_path = "edge_ai/model/best.pt"
            if os.path.exists(local_path):
                print(f"[INFO] Using local weight file: {local_path}")
                model_path = local_path
            else:
                print("[INFO] Falling back to standard COCO pretrained model (yolo11n.pt)...")
                model_path = "yolo11n.pt"

        # Load YOLO model
        self.model = YOLO(model_path)
        print("[SUCCESS] Model loaded successfully.")

    def detect(self, image_frame, conf_threshold=0.25):
        """
        Runs inference on an image path or numpy frame array.
        Returns a list of structured hazard detections.
        """
        results = self.model(image_frame, conf=conf_threshold, verbose=False)
        detections = []

        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                raw_label = self.model.names[cls_id]
                label = self.CLASS_MAPPING.get(raw_label, raw_label)
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].tolist()  # [xmin, ymin, xmax, ymax]

                detections.append({
                    "hazard_type": label,
                    "raw_class": raw_label,
                    "confidence": round(confidence, 4),
                    "bbox": [round(c, 2) for c in bbox]
                })

        return detections

if __name__ == "__main__":
    detector = RoadHazardDetector()
    print("Road Hazard Detector pipeline is ready.")
