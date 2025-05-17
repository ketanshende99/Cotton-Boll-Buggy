# -*- coding: utf-8 -*-
"""
Created on Fri Aug 23 10:53:28 2024

@author: kshende
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
import time

class CottonHarvester:
    def __init__(self, start_lat, start_lon, field_size, bin_capacity, row_spacing):
        self.start_lat = start_lat
        self.start_lon = start_lon
        self.latitude = start_lat
        self.longitude = start_lon
        self.field_size = field_size
        self.bin_capacity = bin_capacity
        self.bin_level = 0
        self.trigger_threshold = 0.8  # 80% of bin capacity
        self.row_spacing = row_spacing / 111111  # Convert meters to degrees (approximate)
        self.current_row = 0
        self.direction = 1  # 1 for East, -1 for West
        self.is_stopped = False  # To stop the harvester when the boll buggy arrives

    def move(self):
        if not self.is_stopped:  # Only move if the harvester is not stopped
            # Move along the current row (East-West direction)
            self.longitude += 0.00001 * self.direction
            
            # Check if we've reached the end of the row
            if abs(self.longitude - self.start_lon) >= self.field_size:
                self.current_row += 1
                self.direction *= -1  # Change direction
                self.latitude += self.row_spacing  # Move to the next row
                self.longitude = self.start_lon if self.direction == 1 else self.start_lon + self.field_size

            # Simulate bin filling
            self.bin_level += np.random.uniform(0, 0.002) * self.bin_capacity
            if self.bin_level > self.bin_capacity:
                self.bin_level = self.bin_capacity

    def get_gps_data(self):
        return {
            'latitude': round(self.latitude, 6),
            'longitude': round(self.longitude, 6),
            'bin_level': round(self.bin_level / self.bin_capacity, 2),
            'trigger': self.bin_level >= self.trigger_threshold * self.bin_capacity
        }

class BollBuggy:
    def __init__(self, start_lat, start_lon):
        self.start_lat = start_lat
        self.start_lon = start_lon
        self.latitude = start_lat
        self.longitude = start_lon
        self.is_moving = False
        self.is_returning = False  # To indicate when the boll buggy is returning
        self.direction = 1
        self.wait_time = 0  # Time to wait for unloading

    def move_towards_harvester(self, harvester_lat, harvester_lon):
        if abs(self.longitude - harvester_lon) > 0.00001:
            self.longitude += 0.00001 * self.direction
        elif abs(self.latitude - harvester_lat) > 0.00001:
            self.latitude += 0.00001 * np.sign(harvester_lat - self.latitude)
        else:
            self.is_moving = False  # Stop moving when at the harvester's position
            self.is_returning = True
            self.wait_time = np.random.uniform(0.5, 1.5)  # Random wait time for unloading

    def move_back(self):
        speed_multiplier = 3  # Increase the speed for returning
        if abs(self.longitude - self.start_lon) > 0.00001:
            self.longitude -= 0.00001 * self.direction * speed_multiplier
        elif abs(self.latitude - self.start_lat) > 0.00001:
            self.latitude -= 0.00001 * np.sign(self.latitude - self.start_lat) * speed_multiplier
        else:
            self.is_returning = False  # Stop moving when back at the start position

class BaseStation:
    def __init__(self):
        self.harvester_data = []

    def receive_data(self, data):
        self.harvester_data.append(data)
        print(f"Received data: {data}")
        if data['trigger']:
            print("ALERT: Bin level above threshold!")

def simulate_radio_communication(harvester, base_station):
    data = harvester.get_gps_data()
    base_station.receive_data(data)
    return data

# Initialize harvester, boll buggy, and base station
harvester = CottonHarvester(start_lat=34.0522, start_lon=-118.2437, field_size=0.01, bin_capacity=1000, row_spacing=10)
boll_buggy = BollBuggy(start_lat=34.0522, start_lon=-118.2437)  # Boll buggy starts at the same position as the harvester
base_station = BaseStation()

# Set up the plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
line1, = ax1.plot([], [], 'ro-', label='Harvester Path')
line2, = ax2.plot([], [], 'b-', label='Bin Level')
boll_buggy_marker, = ax1.plot([], [], 'gs-', label='Boll Buggy Moving to Harvester')
boll_buggy_return_marker, = ax1.plot([], [], 'yo-', label='Boll Buggy Returning')
ax1.set_xlim(harvester.start_lon - 0.001, harvester.start_lon + harvester.field_size + 0.001)
ax1.set_ylim(harvester.start_lat - 0.001, harvester.start_lat + 0.01)
ax2.set_xlim(0, 2000)
ax2.set_ylim(0, 1)
ax1.set_title('Cotton Harvester Simulation')
ax1.set_xlabel('Longitude')
ax1.set_ylabel('Latitude')
ax2.set_xlabel('Time Step')
ax2.set_ylabel('Bin Level')
ax1.legend()
ax2.legend()

x_data, y_data = [], []
bin_levels = []
boll_buggy_x, boll_buggy_y = [], []
boll_buggy_return_x, boll_buggy_return_y = [], []

def update(frame):
    if boll_buggy.is_moving:
        boll_buggy.move_towards_harvester(harvester.latitude, harvester.longitude)
        if not boll_buggy.is_moving:  # Boll buggy reached the harvester
            harvester.is_stopped = True
            time.sleep(boll_buggy.wait_time)  # Simulate unloading
            harvester.bin_level = 0  # Reset bin level after unloading
    elif boll_buggy.is_returning:
        boll_buggy.move_back()
        if len(boll_buggy_x) > 1:
            boll_buggy_return_x.append(boll_buggy.longitude)
            boll_buggy_return_y.append(boll_buggy.latitude)
            boll_buggy_x.pop(0)  # Remove the first position to decrease the trace gradually
            boll_buggy_y.pop(0)
        if not boll_buggy.is_returning:  # Boll buggy returned to its start position
            harvester.is_stopped = False
            boll_buggy_return_x.clear()
            boll_buggy_return_y.clear()
    else:
        harvester.move()
        data = simulate_radio_communication(harvester, base_station)
        if data['trigger']:
            boll_buggy.is_moving = True
            boll_buggy.direction = harvester.direction  # Move in the same direction as the harvester
    
    x_data.append(harvester.longitude)
    y_data.append(harvester.latitude)
    bin_levels.append(harvester.bin_level / harvester.bin_capacity)
    boll_buggy_x.append(boll_buggy.longitude)
    boll_buggy_y.append(boll_buggy.latitude)
    
    line1.set_data(x_data, y_data)
    line2.set_data(range(len(bin_levels)), bin_levels)
    boll_buggy_marker.set_data(boll_buggy_x, boll_buggy_y)
    boll_buggy_return_marker.set_data(boll_buggy_return_x, boll_buggy_return_y)
    
    return line1, line2, boll_buggy_marker, boll_buggy_return_marker

ani = FuncAnimation(fig, update, frames=2000, interval=100, blit=True)
plt.tight_layout()
plt.show()









