# Copyright (c) 2020 Jan Vrany <jan.vrany (a) fit.cvut.cz>
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import sys
import logging

from asyncio import sleep, CancelledError
from bricknil import attach, start
from bricknil.hub import CPlusHub
from bricknil.sensor.motor import CPlusXLMotor, CPlusLargeMotor as CPlusLMotor
#from bricknil.sensor.sensor import PoweredUpAccelerometer, PoweredUpPosition


@attach(CPlusXLMotor, name='motor_a', port=0, capabilities=['sense_speed'])
@attach(CPlusXLMotor, name='motor_b', port=1, capabilities=['sense_speed'])
@attach(CPlusLMotor, name='steering', port=2, capabilities=['sense_pos'])
# @attach(PoweredUpAccelerometer, name='accel', port=97, capabilities=['sense_grv'])
# @attach(PoweredUpPosition, name='position', port=99, capabilities=['sense_pos'])
class Vehicle(CPlusHub):

    def __init__(self, name="4x4 off-roader", query_port_info=False, ble_id=None):
        SteerIncrement = 10
        SpeedIncrement = 30

        super().__init__(name, query_port_info=query_port_info, ble_id=ble_id)
        self.steering_angle = 0
        self.steering_angle_min = 0
        self.steering_angle_max = 0

        self.motor_a_speed = 0
        self.motor_b_speed = 0


    async def get_speed(self):
        return 0
        # return (f_speed + r_speed) / 2

    async def set_speed(self, speed):
        await self.motor_a.set_speed(speed)
        await self.motor_b.set_speed(speed)

    async def motor_a_change(self):
        self.motor_a_speed = self.motor_a.value[CPlusXLMotor.capability.sense_speed]

    async def motor_b_change(self):
        self.motor_b_speed = self.motor_b.value[CPlusXLMotor.capability.sense_speed]

    async def steering_change(self):
        self.steering_angle = self.steering.value[CPlusLMotor.capability.sense_pos]

    async def accel_change(self):
        #self.accel_grv = self.accel.value[PoweredUpAccelerometer.capability.sense_grv]
        #self.accel_cal = self.accel.value[PoweredUpAccelerometer.capability.sense_cal]
        #self.accel_cal = 0
        pass

    async def position_change(self):
        #self.position_pos = self.position.value[PoweredUpPosition.capability.sense_pos]
        #self.accel_cal = self.accel.value[PoweredUpAccelerometer.capability.sense_cal]
        pass

    async def steering_calibrate(self):
        async def wait_until_steering_stop():
            angle0 = self.steering_angle
            while True:
                angle1 = self.steering_angle
                await sleep(0.5)
                angle2 = self.steering_angle
                if angle1 == angle2:# and abs(angle2 - angle0) > 30:
                    break
        await self.steering.set_speed(50)
        # await self.steering.rotate(1000, 50)
        await wait_until_steering_stop()
        self.steering_angle_max = self.steering_angle
        print("I: steering_calibrate - right stop: %s" % self.steering_angle_max)

        await self.steering.set_speed(-50)
        # await self.steering.rotate(1000,-50)
        await wait_until_steering_stop()
        self.steering_angle_min = self.steering_angle
        print("I: steering_calibrate - left stop: %s" % self.steering_angle_min)

        zero = int((self.steering_angle_max + self.steering_angle_min) / 2)
        half = abs(self.steering_angle_max - zero)
        # Now, adjust min and max by 10% to avoid servo motor to try
        # to go beyond steering stop (which relies on hub cutting the power
        # to avoid motor damage)
        self.steering_angle_min = self.steering_angle_min + int(0.1 * half)
        self.steering_angle_max = self.steering_angle_max - int(0.1 * half)

        print("I: steering_calibrate %s (zero) %s (min) %s (max)" % (zero, self.steering_angle_min, self.steering_angle_max))
        await self.steering.set_pos(zero, speed=10)
        await sleep(2)

    async def steer(self, pct, speed=60):
        zero = int((self.steering_angle_min + self.steering_angle_max) / 2)
        half = abs(self.steering_angle_max - zero)
        pos = zero + int((pct / 100) * half)

        print("I: steer %s (pct) %s (zero) %s (half) %s (pos)" % (pct, zero, half, pos))
        await self.steering.set_pos(pos, speed=speed)

    async def speed(self, pct):
        """
        Set speed in perctentage, 100 is full speed forward,
        -100 is full speed reversing
        """
        await self.motor_a.set_speed(-1*pct)
        await self.motor_b.set_speed(-1*pct)

    async def run(self):
        # await sleep(15)

        await self.steering_calibrate()

        try:
            while True:
                await sleep(15)
        except CancelledError:
            pass
