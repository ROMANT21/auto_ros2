import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import ParameterDescriptor
import cv2 as cv

# Used to convert OpenCV Mat type to ROS Image type
# NOTE: This may not be the most effective, we could turn the image into an JPEG string or even define a custom ROS data type.
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


# *PARAMETERS*
# cap: DEFAULT = cv.VideoCapture(0)
# fps: DEFAULT = 30
# topic name: DEFAULT = 'image'
# run node with parameters: ros2 run aruco_node aruco_node --ros-args -p fps:=30
class ImageCaptureNode(Node):
    def __init__(self):
        super().__init__("image_capture")
        # Declare the parameters for the node
        self.cam_fps = (
            self.declare_parameter(
                "cam_fps",
                30,
                ParameterDescriptor(
                    description="The frames per second (FPS) of the camera you're capturing from",
                    read_only=True,
                ),
            )
            .get_parameter_value()
            .integer_value
        )
        self.cam_idx = (
            self.declare_parameter(
                "cam_idx",
                0,
                ParameterDescriptor(
                    description="The camera index which defines which camera to capture from",
                    read_only=True,
                ),
            )
            .get_parameter_value()
            .integer_value
        )

        # Create a camera capture device given a camera index
        self.cap = cv.VideoCapture(self.cam_idx)
        if not self.cap.isOpened():
            self.get_logger().info("Could not open camera")
            exit()

        # Define the image publisher
        self.publisher_ = self.create_publisher(Image, "image", 10)
        self.bridge = CvBridge()

        # Capture and publish frames at a certain fps
        self.timer = self.create_timer(1.0 / self.cam_fps, self.publish_image)

    def publish_image(self):
        # Capture frame from camera
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().error("Failed to capture image")
            return

        # Convert cv2 Mat to ROS Image message
        ros_image = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")

        # Publish image
        self.publisher_.publish(ros_image)
        self.get_logger().info("Published an image")

    def close_video_capture(self):
        if self.cap:
            self.cap.release()
            self.get_logger().info(f"Closed video capture device")


def main(args=None):
    rclpy.init(args=args)

    image_capture_node = ImageCaptureNode()

    try:
        rclpy.spin(image_capture_node)
    except KeyboardInterrupt:
        pass
    finally:
        image_capture_node.close_video_capture()

        # Destroy the node explicitly
        # (optional - otherwise it will be done automatically
        # when the garbage collector destroys the node object)
        image_capture_node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
