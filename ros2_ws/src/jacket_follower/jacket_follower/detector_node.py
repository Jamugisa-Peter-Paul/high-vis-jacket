"""Jacket detector node.

Subscribes : /camera/image_raw            (sensor_msgs/Image)
Publishes  : /jacket/detections           (vision_msgs/Detection2DArray)  all jackets above the confidence threshold
             /jacket/debug_image          (sensor_msgs/Image)              camera frame with boxes drawn
             /jacket/inference_ms         (std_msgs/Float32)               model latency per frame
"""
import time

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import Float32
from vision_msgs.msg import Detection2D, Detection2DArray, ObjectHypothesisWithPose


class JacketDetector(Node):
    def __init__(self):
        super().__init__("jacket_detector")
        self.declare_parameter("model_path", "models/jacket_finetuned_v2.pt")
        self.declare_parameter("conf_threshold", 0.40)
        self.declare_parameter("iou_threshold", 0.50)
        self.declare_parameter("imgsz", 320)
        self.declare_parameter("device", "cuda:0")
        self.declare_parameter("crop_bottom_px", 0)        # real robot: hide the gripper fingertips
        self.declare_parameter("publish_debug_image", True)

        from ultralytics import YOLO                         # imported here so `ros2 run --help` stays fast
        p = self.get_parameter
        self.model = YOLO(p("model_path").value)
        self.conf = float(p("conf_threshold").value)
        self.iou = float(p("iou_threshold").value)
        self.imgsz = int(p("imgsz").value)
        self.device = p("device").value
        self.crop = int(p("crop_bottom_px").value)
        self.debug = bool(p("publish_debug_image").value)

        self.bridge = CvBridge()
        self.pub_det = self.create_publisher(Detection2DArray, "/jacket/detections", 10)
        self.pub_img = self.create_publisher(Image, "/jacket/debug_image", 2)
        self.pub_ms = self.create_publisher(Float32, "/jacket/inference_ms", 10)
        self.create_subscription(Image, "/camera/image_raw", self.on_image, qos_profile_sensor_data)
        self.busy = False
        self.get_logger().info(f"model={p('model_path').value} conf={self.conf} imgsz={self.imgsz} device={self.device}")

    def on_image(self, msg):
        if self.busy:                                        # drop frames rather than queue them (keeps latency low)
            return
        self.busy = True
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            if self.crop > 0:
                frame[-self.crop:] = 0
            t0 = time.perf_counter()
            r = self.model.predict(frame, imgsz=self.imgsz, conf=self.conf, iou=self.iou,
                                   device=self.device, verbose=False)[0]
            ms = (time.perf_counter() - t0) * 1000.0

            out = Detection2DArray()
            out.header = msg.header
            for (x1, y1, x2, y2), c in zip(r.boxes.xyxy.cpu().numpy(), r.boxes.conf.cpu().numpy()):
                d = Detection2D()
                d.header = msg.header
                d.bbox.center.position.x = float((x1 + x2) / 2)
                d.bbox.center.position.y = float((y1 + y2) / 2)
                d.bbox.size_x = float(x2 - x1)
                d.bbox.size_y = float(y2 - y1)
                h = ObjectHypothesisWithPose()
                h.hypothesis.class_id = "safety_jacket"
                h.hypothesis.score = float(c)
                d.results.append(h)
                out.detections.append(d)
                if self.debug:
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 255), 2)
                    cv2.putText(frame, "jacket %.2f" % c, (int(x1), max(15, int(y1) - 6)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            self.pub_det.publish(out)
            self.pub_ms.publish(Float32(data=ms))
            if self.debug:
                cv2.putText(frame, "%d jackets  %.0f ms" % (len(out.detections), ms), (8, 22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                img = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
                img.header = msg.header
                self.pub_img.publish(img)
        finally:
            self.busy = False


def main():
    rclpy.init()
    node = JacketDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
