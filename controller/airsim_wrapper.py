import time
from typing import Tuple

import nest_asyncio
nest_asyncio.apply()

import airsim
import numpy as np
import cv2
import threading

from .abs.robot_wrapper import RobotWrapper
from .utils import print_t
import traceback

MOVEMENT_MIN = 200
MOVEMENT_MAX = 1000

SCENE_CHANGE_DISTANCE = 300

DEFAULT_SPEED = 5

def adjust_exposure(img, alpha=1.0, beta=0):
    """
    Adjust the exposure of an image.
    
    :param img: Input image
    :param alpha: Contrast control (1.0-3.0). Higher values increase exposure.
    :param beta: Brightness control (0-100). Higher values add brightness.
    :return: Exposure adjusted image
    """
    # Apply exposure adjustment using the formula: new_img = img * alpha + beta
    new_img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
    return new_img

def sharpen_image(img):
    """
    Apply a sharpening filter to an image.
    
    :param img: Input image
    :return: Sharpened image
    """
    # Define a sharpening kernel
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]])
    
    # Apply the sharpening filter
    sharpened = cv2.filter2D(img, -1, kernel)
    return sharpened

class FrameReader:
    def __init__(self, fr):
        # Initialize the video capture
        self.fr = fr

    @property
    def frame(self):
        # Read a frame from the video capture
        frame = self.fr
        frame = adjust_exposure(frame, alpha=1.3, beta=-30)
        return sharpen_image(frame)


def cap_distance(distance):
    if distance < MOVEMENT_MIN:
        return MOVEMENT_MIN
    elif distance > MOVEMENT_MAX:
        return MOVEMENT_MAX
    return distance


class AirSimWrapper(RobotWrapper):
    def __init__(self):
        self.client = airsim.MultirotorClient()
        self.image_client = airsim.MultirotorClient()
        self.image_queue = {}
        self.camera_name = '0'
        self.setup_image_request()

    def setup_image_request(self):
         self.image_queue = []

    def _capture_images(self):
        while self.is_running:
            responses = self.image_client.simGetImages(
                [airsim.ImageRequest(self.camera_name, airsim.ImageType.Scene, pixels_as_float=False, compress=False)]
            )
            for i, response in enumerate(responses):
                img_np_array = np.frombuffer(response.image_data_uint8, dtype=np.uint8).reshape(response.height, response.width, 3)
                self.image_queue.append(img_np_array)
            time.sleep(0.02)  # Adjust as needed

    def connect(self):
        print("AirSim Wrapper: Connecting to AirSim...")
        try:
            self.client.confirmConnection()
            self.image_client.confirmConnection()
            print_t("AirSim Wrapper: Connection confirmed.")
            self.client.enableApiControl(True)
            self.image_client.enableApiControl(True)
            self.api_control_enabled = True
            print_t("AirSim Wrapper: API control enabled.")
            self.client.armDisarm(True)
            self.is_armed = True
            print_t("AirSim Wrapper: Drone armed.")
            self.is_connected = True 
            print_t("AirSim Wrapper: Successfully connected and armed.")
            self.is_running = True
            self.image_thread = threading.Thread(target=self._capture_images)
            self.image_thread.daemon = True
            self.image_thread.start()
        
        except Exception as e:
            print_t(f"AirSim Wrapper: Connection failed - {e}")
            print_t(traceback.format_exc())
            self.is_connected = False
            self.api_control_enabled = False
            self.is_armed = False

    def keep_active(self):
        #  AirSim handles its own 'keep-alive'
        pass

    def takeoff(self) -> bool:
       self.client.takeoffAsync().join()
       return True
       


    def land(self):
        self.client.landAsync().join()

    def start_stream(self):
         print("AirSim stream started")

    def stop_stream(self):
        self.is_running = False
        self.image_thread.join()
        print("AirSim stream stopped")

    def get_frame_reader(self):  # Default to front camera
        if not self.is_running:
            return None
        return FrameReader(self.image_queue[-1])

    def move_forward(self, distance: int, speed=DEFAULT_SPEED) -> Tuple[bool, bool]:
        # AirSim uses meters, convert cm to meters
        distance = cap_distance(distance)
        distance_m = distance / 100.0
        current_pose = self.client.simGetVehiclePose().position
        target_x = current_pose.x_val + distance_m
        self.client.moveToPositionAsync(target_x, current_pose.y_val, current_pose.z_val, speed).join()
        self.movement_x_accumulator += distance
        return True, distance > SCENE_CHANGE_DISTANCE

    def move_backward(self, distance: int, speed=DEFAULT_SPEED) -> Tuple[bool, bool]:
        distance = cap_distance(distance)
        distance_m = distance / 100.0
        current_pose = self.client.simGetVehiclePose().position
        target_x = current_pose.x_val - distance_m
        self.client.moveToPositionAsync(target_x, current_pose.y_val, current_pose.z_val, DEFAULT_SPEED).join()
        self.movement_x_accumulator -= distance
        return True, distance > SCENE_CHANGE_DISTANCE

    def move_left(self, distance: int, speed=DEFAULT_SPEED) -> Tuple[bool, bool]:
        distance = cap_distance(distance)
        distance_m = distance / 100.0
        current_pose = self.client.simGetVehiclePose().position
        target_y = current_pose.y_val + distance_m
        self.client.moveToPositionAsync(current_pose.x_val, current_pose.y_val, current_pose.z_val, DEFAULT_SPEED).join()
        self.client.moveToPositionAsync(current_pose.x_val, target_y, current_pose.z_val, 5).join()
        self.movement_y_accumulator += distance
        return True, distance > SCENE_CHANGE_DISTANCE

    def move_right(self, distance: int, speed=DEFAULT_SPEED) -> Tuple[bool, bool]:
        distance = cap_distance(distance)
        distance_m = distance / 100.0
        current_pose = self.client.simGetVehiclePose().position
        target_y = current_pose.y_val - distance_m
        self.client.moveToPositionAsync(current_pose.x_val, current_pose.y_val, current_pose.z_val, DEFAULT_SPEED).join()
        self.client.moveToPositionAsync(current_pose.x_val, target_y, current_pose.z_val, 5).join()
        self.movement_y_accumulator -= distance
        return True, distance > SCENE_CHANGE_DISTANCE

    def move_up(self, distance: int, speed=DEFAULT_SPEED) -> Tuple[bool, bool]:
        distance = cap_distance(distance)
        distance_m = distance / 100.0
        current_pose = self.client.simGetVehiclePose().position
        target_z = current_pose.z_val - distance_m  # AirSim Z is inverted
        self.client.moveToPositionAsync(current_pose.x_val, current_pose.y_val, target_z, DEFAULT_SPEED).join()
        return True, False

    def move_down(self, distance: int, speed=DEFAULT_SPEED) -> Tuple[bool, bool]:
        distance = cap_distance(distance)
        distance_m = distance / 100.0
        current_pose = self.client.simGetVehiclePose().position
        target_z = current_pose.z_val + distance_m
        self.client.moveToPositionAsync(current_pose.x_val, current_pose.y_val, target_z, DEFAULT_SPEED).join()
        return True, False

    def turn_ccw(self, degree: int) -> Tuple[bool, bool]:
        current_orientation = self.client.simGetVehiclePose().orientation
        #  Quaternions to Euler (yaw-pitch-roll)
        pitch, roll, yaw = airsim.to_eularian_angles(current_orientation)
        target_yaw = yaw + np.radians(degree)
        self.client.rotateToYawAsync(np.degrees(target_yaw), 5).join()
        self.rotation_accumulator += degree
        return True, False

    def turn_cw(self, degree: int) -> Tuple[bool, bool]:
        current_orientation = self.client.simGetVehiclePose().orientation
        pitch, roll, yaw = airsim.to_eularian_angles(current_orientation)
        target_yaw = yaw - np.radians(degree)
        self.client.rotateToYawAsync(np.degrees(target_yaw), 5).join()
        self.rotation_accumulator -= degree
        return True, False

    def speed_up(self, degree: int) -> bool:
        DEFAULT_SPEED += 300
        return True, False

    def drop_goods(self, finish: int) -> bool:
         pass

    def carry_goods(self, finish: int) -> bool:
        pass

if __name__ == "__main__":
    drone = None # Initialize drone variable outside try block
    try:
        print("Creating AirSimWrapper instance...")
        # Instantiate the wrapper
        drone = AirSimWrapper() 

        print("\nAttempting to connect...")
        # Connect to the simulator and enable API control
        drone.connect() 
        
        # Check if connection was successful before proceeding
        if not drone.is_connected:
             print("Connection failed. Exiting.")
             
        print("\nStarting Stream (Note: Image capture thread already started on connect)...")
        # The image thread starts automatically on connect in your current code
        # This call is mainly for semantic consistency if needed elsewhere
        drone.start_stream() 

        print("\nAttempting takeoff...")
        # Command takeoff
        if drone.takeoff(): 
            print("Takeoff successful.")
            
            print("\nWaiting for 5 seconds...")
            time.sleep(5)

            # --- Test Movement (Optional) ---
            print("\nAttempting to move forward 50 cm (0.5m)...")
            # Move forward
            drone.move_forward(50) 
            print("Move forward command sent.")
            time.sleep(3) # Wait for move to likely complete

            print("\nAttempting to turn CW 90 degrees...")
            # Turn clockwise
            drone.turn_cw(90) 
            print("Turn CW command sent.")
            time.sleep(3) # Wait for turn to likely complete
            # --- End Test Movement ---

            # --- Test Get Frame (Optional) ---
            print("\nAttempting to get a frame...")
            # Get a frame
            frame = drone.get_frame_reader("0") # Use the camera name defined in your wrapper
            if frame is not None:
                print(f"Successfully retrieved frame with shape: {frame.shape}")
                # You could display it using OpenCV here if needed:
                # import cv2
                # cv2.imshow("AirSim Frame", frame)
                # cv2.waitKey(1000) # Display for 1 second
                # cv2.destroyAllWindows()
            else:
                print("Could not retrieve frame (queue might be empty or stream stopped).")
            # --- End Test Get Frame ---

            print("\nAttempting to land...")
            # Land the drone
            drone.land() 
            print("Landing command sent.")
            time.sleep(5) # Give time for landing

        else:
            print("Takeoff failed or was skipped.")

    except Exception as e:
        print(f"\n--- An error occurred during the test ---")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {e}")
        print("Traceback:")
        print(traceback.format_exc())
        print("------------------------------------------")

    finally:
        if drone and drone.is_connected:
            print("\nStopping stream and cleaning up...")
            # Stop the image capture thread
            drone.stop_stream() 
            # Consider adding arm/disarm and disableApiControl if needed for full cleanup
            # drone.client.armDisarm(False)
            # drone.client.enableApiControl(False) 
            print("Cleanup complete.")
        else:
            print("\nNo active connection to clean up or drone not initialized.")