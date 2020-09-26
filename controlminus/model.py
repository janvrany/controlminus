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
from bricknil.sensor.sensor import PoweredUpHubIMUPosition, PoweredUpHubIMUAccelerometer, PoweredUpHubIMUGyro, VoltageSensor, CurrentSensor


@attach(CPlusXLMotor, name='motor_a', port=0, capabilities=[('sense_speed', 5), ('sense_load', 5), ('sense_power', 5)])
@attach(CPlusXLMotor, name='motor_b', port=1, capabilities=[('sense_speed', 5), ('sense_load', 5), ('sense_power', 5)])
@attach(CPlusLMotor, name='steering', port=2, capabilities=[('sense_pos', 1), ('sense_speed', 5), ('sense_load', 5), ('sense_power', 5)])
@attach(PoweredUpHubIMUAccelerometer, name='accel', capabilities=[('sense_grv', 5)])
@attach(PoweredUpHubIMUGyro, name='gyro', capabilities=[('sense_rot', 5)])
@attach(PoweredUpHubIMUPosition, name='position', port=99, capabilities=[('sense_pos', 2)])
@attach(VoltageSensor, name='voltage', capabilities=[('sense_l', 10)])
@attach(CurrentSensor, name='current', capabilities=[('sense_l', 10)])
class Vehicle(CPlusHub):

    def __init__(self, name="4x4 off-roader", query_port_info=False, ble_id=None):
        SteerIncrement = 10
        SpeedIncrement = 30

        super().__init__(name, query_port_info=query_port_info, ble_id=ble_id)
        self.steering_angle = 0
        self.steering_target = 0
        self.steering_angle_min = 0
        self.steering_angle_max = 0
        self.steering_calibration_in_process = False

        self.motor_a_speed = 0
        self.motor_b_speed = 0


    async def get_speed(self):
        return 0
        # return (f_speed + r_speed) / 2

    async def set_speed(self, speed):
        await self.motor_a.set_speed(speed)
        await self.motor_b.set_speed(speed)

    async def steering_change(self):
        self.steering_angle = self.steering.sense_pos
        # steering_speed = self.steering.sense_speed
        # print("I: steering pos: %s, target %s" % (self.steering_angle, self.steering_target))
        # if self.steering_calibration_in_process:
        #     return
        # diff = 0
        # if (abs(self.steering_target) - diff) <= abs(self.steering_angle) and abs(self.steering_angle) <= (abs(self.steering_target) + diff):
        #     if steering_speed != 0:
        #         await self.steering.set_speed(0)

    async def steering_calibrate(self):
        async def wait_until_steering_stop():
            angle1 = 100000
            angle2 = self.steering_angle
            while angle1 != angle2:
                angle1 = angle2
                await sleep(1)
                angle2 = self.steering_angle
        await self.steering.reset_pos();

        self.steering_calibration_in_process = True
        # await self.steering.set_speed(60)
        await self.steering.rotate(180, 50, 100)
        await wait_until_steering_stop()
        self.steering_angle_max = self.steering_angle
        print("I: steering_calibrate - right stop: %s" % self.steering_angle_max)

        # await self.steering.set_speed(-60)
        await self.steering.rotate(180,-50, 100)
        await wait_until_steering_stop()
        self.steering_angle_min = self.steering_angle
        print("I: steering_calibrate - left stop: %s" % self.steering_angle_min)

        zero = int( (self.steering_angle_max + self.steering_angle_min) / 2)
        half = int( abs(self.steering_angle_max - self.steering_angle_min) / 2 )
        # Now, adjust min and max by 5% to avoid servo motor to try
        # to go beyond steering stop (which relies on hub cutting the power
        # to avoid motor damage)
        half = int(1 * half)

        self.steering_angle_min = zero - half
        self.steering_angle_max = zero + half

        print("I: steering_calibrate 1: %s (zero) %s (min) %s (max)" % (zero, self.steering_angle_min, self.steering_angle_max))

        await self.steering.set_pos(zero, speed=50)
        await sleep(2)

        await self.steering.reset_pos()
        zero = 0
        self.steering_angle_min = -half
        self.steering_angle_max = +half
        self.steering_target = 0
        print("I: steering_calibrate 2: %s (zero) %s (min) %s (max)" % (zero, self.steering_angle_min, self.steering_angle_max))

        await sleep(2)
        self.steering_calibration_in_process = False

    async def steer(self, pct, speed=60):
        if abs(pct) < 10:
            pct = 0
        
        zero = int((self.steering_angle_min + self.steering_angle_max) / 2)
        half = abs(self.steering_angle_max - zero)
        new_target = zero + int((pct / 100) * half)
        if new_target != 0 and abs(new_target - self.steering_target) < 5:
            return

        self.steering_target = zero + int((pct / 100) * half)
        #breakpoint()
        diff = abs(self.steering_target - self.steering.sense_pos)
        speed = int((diff / half) * speed)

        print("I: steering_target = %d, speed = %d" % (self.steering_target, speed))

        await self.steering.set_pos(self.steering_target, speed=speed, max_power=100)

    async def speed(self, pct):
        """
        Set speed in perctentage, 100 is full speed forward,
        -100 is full speed reversing
        """
        #await self.motor_a.set_speed(-1*pct)
        #await self.motor_b.set_speed(-1*pct)
        if abs(pct) < 10:
            await self.motor_a.set_speed(0)
            await self.motor_b.set_speed(0)
        else:
            await self.motor_a.ramp_speed2(-1*pct,500)
            await self.motor_b.ramp_speed2(-1*pct,500)

    async def run(self):
        # await sleep(15)
        # self.position.connect("notify", self.on_notify)

        await self.steering_calibrate()

        try:
            pass
            # while True:
            #     await sleep(15)
        except CancelledError:
            pass
