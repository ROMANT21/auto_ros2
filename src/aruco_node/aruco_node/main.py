import rclpy
from rclpy.action import ActionServer
from rclpy.executors import MultiThreadedExecutor
# import matplotlib.pyplot as plt
from rclpy.node import Node
import cv2 as cv
import cv2.aruco as aruco
# import os
import numpy as np
from loguru import logger as llogger
from typing import (Callable, Dict)
from dataclasses import dataclass
#
# Used to convert OpenCV Mat type to ROS Image type
# NOTE: This may not be the most effective, we could turn the image into an JPEG string or even define a custom ROS data type.
import rclpy.publisher
import rclpy.subscription
from sensor_msgs.msg import Image as RosImage
from cv_bridge import CvBridge
from custom_interfaces.action import TrackArucoMarker

# A map of aruco dictionary strings to opencv.aruco enum values
aruco_dict_map = {
    "4x4_50": aruco.DICT_4X4_50,
    "4x4_100": aruco.DICT_4X4_100,
    "4x4_250": aruco.DICT_4X4_250,
    "4x4_1000": aruco.DICT_4X4_1000,
    "5x5_50": aruco.DICT_5X5_50,
    "5x5_100": aruco.DICT_5X5_100,
    "5x5_250": aruco.DICT_5X5_250,
    "5x5_1000": aruco.DICT_5X5_1000,
    "6x6_50": aruco.DICT_6X6_50,
    "6x6_100": aruco.DICT_6X6_100,
    "6x6_250": aruco.DICT_6X6_250,
    "6x6_1000": aruco.DICT_6X6_1000,
    "7x7_50": aruco.DICT_7X7_50,
    "7x7_100": aruco.DICT_7X7_100,
    "7x7_250": aruco.DICT_7X7_250,
    "7x7_1000": aruco.DICT_7X7_1000
}

latest_image: cv.Mat | None = None
"""The latest image received from the image subscriber (converted from RosImage to cv2.Mat)."""

#image_publisher: rclpy.publisher.Publisher | None = None

async def track_aruco_marker_callback(goal_handle: Callable):
    marker_id = goal_handle.request.marker_id
    llogger.debug(f"Tracking Aruco marker with id {marker_id}...")

    # TODO: Warn or reject action if there is no image topic to get images from

    # Try to track the aruco tag
    while True:
        # Create a new feedback message
        #llogger.debug("Executing action")
        """
        feedback = TrackArucoMarker.Feedback()
        feedback.marker_transform.header.frame_id = "camera"
        feedback.marker_transform.child_frame_id = f"marker_{marker_id}"
        feedback.marker_in_view = False
        # TODO: Eventually fill sec and nanosec in marker_transform using ROS libraries

        if self.latest_image is not None:
            self.publisher_.publish(self.latest_ros_image)
            # Check for aruco markers in the frame
            marker_corners, marker_ids = self.detect_aruco_markers(self.latest_image)
            self.get_logger().info(f"Found the follwing markers in the frame: {marker_ids}")
            self.get_logger().info(f"Found the follwing markers in the frame: {marker_corners}")


        goal_handle.publish_feedback(feedback)
        # TODO This probably isn't the best solution lol
        self.tracking_rate.sleep()
        """

    return None

async def image_callback(image_msg: RosImage):
    """ Store the latest image for proccesing. """
    try:
        # Convert ROS2 Image to OpenCV format
        #cv_image = self.bridge.imgmsg_to_cv2(image_msg, desired_encoding='bgr8')
        #latest_image = cv_imageexecute_callback
        #self.get_logger().info("Received Image")
        llogger.debug("Received Image")
        image_publisher.publish(latest_image)

    except Exception as e:
        #self.get_logger().error(f"Error processing image: {e}")
        llogger.error(f"Error processing image: {e}")


@dataclass(kw_only=True)
class ArucoNode(Node):
    """
    When <TODO: started or action start msg recv'd?>, this node will begin
    searching for ArUco markers in the environment. <TODO: see above> will 
    provide a marker ID to find.
    
    If any marker is found, it sends feedback displaying which markers are
    currently in frame.
    
    <b>
    This <TODO: action/node> runs until stopped by the Navigator node.
    <TODO: how?> It's up to the caller to stop this node when we're close
    enough to the goal.
    
    In other words, the ArUco Node isn't making the calls - the Navigator
    manages us!
    </b>
    """
    
    camera_config_file: str
    """Filename of the config file."""
    
    aruco_dict_map: Dict
    """The set of marker's we're looking for"""
    
    aruco_dict: str
    """Name of that set."""
    
    marker_length: float
    """Size of marker in meters."""
    
    aruco_detector: aruco.ArucoDetector
    """Detects aruco markers."""
    
    detector_params: aruco.DetectorParameters
    """Used to change the defaults in the detector's initializer."""
    
    immage_subscription: rclpy.subscription.Subscription
    """Image subscriber for aruco."""
    
    bridge = CvBridge()
    """Converts images from ROS to cv2.Mat types"""
    

    def __init__(self):
        super().__init__("aruco_node")
        # Declare the parameters for the node
        from rcl_interfaces.msg import ParameterDescriptor
        self.camera_config_file = self.declare_parameter('camera_config_file', 'cam.yml',
            ParameterDescriptor(
                description="The camera config .yml file that contains camera matrix, distance coefficients, and reprojection error",
                read_only=True
            )
        ).get_parameter_value().string_value
        self.aruco_dict = self.declare_parameter('aruco_dict', "4x4_50", # correlates to URC standard dictionary
           ParameterDescriptor(
                description="This is the aruco dictionary number to assume aruco tags are from which come from 'cv2.aruco' predefined dictionary enum",
           )
        ).get_parameter_value().string_value
        self.marker_length = self.declare_parameter('marker_length', 0.175, # correlates to URC standard marker length
           ParameterDescriptor(
                description="This is the length (in meters) of the one side of the aruco marker you are tring to detect (not including white border).",
           )
        ).get_parameter_value().double_value

        # Camera calibration configuration
        #(
        # self.camera_mat,
        # self.dist_coeffs,
        # self.rep_error
        #) = self.read_camera_config_file()
        #self.get_logger().info("Finished reading calibration information for camera")

        # TODO: For testing
        #image_publisher = self.create_publisher(RosImage, 'aruco_tracking_image', 10)

        # Aruco detector configuration
        self.detector_params = aruco.DetectorParameters() # TODO: Look into this
        self.tracker = aruco.ArucoDetector(
            aruco.getPredefinedDictionary(aruco_dict_map[self.aruco_dict]),
            self.detector_params
        )
        self.obj_points = np.array([ # Real world 3D coordinates of the marker corners
            [-self.marker_length / 2, 0,  self.marker_length / 2], # Top-left
            [ self.marker_length / 2, 0,  self.marker_length / 2], # Top-right
            [ self.marker_length / 2, 0, -self.marker_length / 2], # Bottom-right
            [-self.marker_length / 2, 0, -self.marker_length / 2], # Bottom-left
        ])
        llogger.info("Finished creating aruco tracker")

        # Subscriber configuration
        # TODO: Should we crash if we can't connect to image topic?
        # self.latest_image = None # Most recent video capture frame from subscriber
        self.image_subscription = self.create_subscription(
            RosImage, 'image', image_callback, 1
        )
        llogger.info("Finished creating image subscriber")

        # Action-server configuration
        self._action_server = ActionServer(
            self,
            TrackArucoMarker,
            'track_aruco_marker',
            track_aruco_marker_callback,
        )
        llogger.info("Finished creation action-server for aruco tracking")


        ## Detect the marker ids
        #marker_corners, marker_ids = self.detect_aruco_markers(cv_image)

        #cv_detection_image = aruco.drawDetectedMarkers(cv_image, 
        #                                               marker_corners,
        #                                               marker_ids)
        ## Calculate pose for each marker
        #if (marker_ids is not None and len(marker_ids) != 0):
        #    for img_points in marker_corners:
        #        retval, rvec, tvec = self.calculate_pose(img_points)
        
    def detect_aruco_markers(self, image: RosImage):
        """Given an image, return detected aruco markers and rejected markers (candidates for aruco markers)"""
        # Detect markers (corners and ids) and possible corners (rejected)
        (
         detected_marker_corners,
         detected_marker_ids,
         rejected_marker_ids
        ) = self.tracker.detectMarkers(image)
        return detected_marker_corners, detected_marker_ids

    def calculate_pose(self, img_points):
        """Given a set of image points (detected aruco corners), return the pose for the marker"""
        img_points = np.array(img_points, dtype=np.float32).reshape(4, 2)
        retval, rvec, tvec = cv.solvePnP(
            self.obj_points, img_points, self.camera_mat, self.dist_coeffs
        )
        return retval, rvec, tvec
    
    def read_camera_config_file(self):
        """Read the camera configuration file and return parameters"""
        
        # Try to open camera config file
        fs = cv.FileStorage(self.camera_config_file, cv.FILE_STORAGE_READ)
        if not fs.isOpened():
            llogger.error(f"Error opening camrea config file at {self.camera_config_file}")
            exit(1)

        camera_mat = fs.getNode("camera_matrix").mat()
        dist_coeffs = fs.getNode("dist_coeffs").mat()
        rep_error = fs.getNode("reproj_error").real()
        fs.release()

        return camera_mat, dist_coeffs, rep_error

    def __hash__(self) -> int:
        return super().__hash__()
        
def main(args=None):
    """Handle spinning up and destroying a node"""
    rclpy.init(args=args)
    aruco_node = ArucoNode()
    executor = MultiThreadedExecutor()
    executor.add_node(aruco_node)

    try:
        #rclpy.spin(aruco_node)
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        # Destroy the node explicitly
        # (optional - otherwise it will be done automatically
        # when the garbage collector destroys the node object)
        aruco_node.destroy_node()
        rclpy.shutdown()



if __name__ == "__main__":
    main()
