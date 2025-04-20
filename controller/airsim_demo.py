import airsim
import os

# connect to the AirSim simulator
client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)
client.armDisarm(True)

# Async methods returns Future. Call join() to wait for task to complete.
client.takeoffAsync().join()
client.moveToPositionAsync(50, 0, -7, 5).join()

# take images
responses = client.simGetImages([
    airsim.ImageRequest("0", airsim.ImageType.Scene, pixels_as_float=False, compress=False),
    airsim.ImageRequest("1", airsim.ImageType.Scene, pixels_as_float=False, compress=False)])
print('Retrieved images: %d', len(responses))

# do something with the images
for response in responses:
    if response.pixels_as_float:
        print("Type %d, size %d" % (response.image_type, len(response.image_data_float)))
        airsim.write_pfm(os.path.normpath('assets/temp/py1.pfm'), airsim.get_pfm_array(response))
    else:
        print("Type %d, size %d" % (response.image_type, len(response.image_data_uint8)))
        airsim.write_file(os.path.normpath('assets/temp/py2.png'), response.image_data_uint8)

client.landAsync().join()