#!/usr/bin/env python3
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
from ultralytics import YOLO

class VisionDetector(Node):
    def __init__(self):
        super().__init__('vision_detector')

        # --- 加载 YOLO 模型 ---
        model_path = '/mnt/d/python_project/sam2-main/yolov8n.pt'
        self.model = YOLO(model_path)
        self.get_logger().info(f'YOLO model loaded: {model_path}')

        # --- cv_bridge 转换器 ---
        self.bridge = CvBridge()

        # --- 订阅摄像头话题 ---
        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        # --- 发布画框后的图像 ---
        self.image_pub = self.create_publisher(Image, '/detection_image', 10)

        # --- 发布检测结果文本 ---
        self.result_pub = self.create_publisher(String, '/detections', 10)

        self.get_logger().info('Vision Detector node started, waiting for images...')

    def image_callback(self, msg: Image):
        # ① ROS Image → OpenCV
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # ② YOLO 推理（每 3 帧跑一次，省算力）
        if not hasattr(self, '_frame_count'):
            self._frame_count = 0
        self._frame_count += 1
        if self._frame_count % 3 != 0:
            return
        results = self.model(frame, verbose=False)

        # ③ 画检测框
        annotated = results[0].plot()

        # ④ 发布画框图像
        img_msg = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
        img_msg.header = msg.header  # 时间戳对齐
        self.image_pub.publish(img_msg)

        # ⑤ 发布检测结果文本
        detections = []
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            label = results[0].names[cls_id]
            detections.append(f'{label}({conf:.2f})')

        if detections:
            text = ' | '.join(detections)
            self.result_pub.publish(String(data=text))
            self.get_logger().info(f'Detected: {text}')
        else:
            # 不在终端刷屏，安静跳过
            pass

def main():
    rclpy.init()
    node = VisionDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
