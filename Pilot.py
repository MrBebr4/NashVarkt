import numpy
import time
import krpc
import matplotlib.pyplot as plt
import math
import json

# Настройки гравитационного поворота
turn_start_altitude = 250
turn_end_altitude = 100000
target_altitude = 180000

# Установка соединения с игрой
conn = krpc.connect(name='Запуск на орбиту')
vessel = conn.space_center.active_vessel

# Создание потоков для данных
ut = conn.add_stream(getattr, conn.space_center, 'ut')
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
speed = conn.add_stream(getattr, vessel.flight(vessel.orbit.body.reference_frame), 'speed')
mass = conn.add_stream(getattr, vessel, 'mass')
stage_5_resources = vessel.resources_in_decouple_stage(stage=5-1, cumulative=False)
srb_fuel = conn.add_stream(stage_5_resources.amount, 'SolidFuel')

# Списки для сохранения данных
time_data = []
altitude_data = []
speed_data = []
mass_data = []
pastime = []
height = []
velocity = []
acceleration = []

# Настройки для записи данных
last_record_time = 0
record_interval = 0.1  # Шаг записи 0.1 секунды

# Записываем начальное время
start_time = ut()

# Функция для записи данных
def record_data():
    global last_record_time, start_time
    current_time = ut() - start_time  # Корректируем время
    if current_time - last_record_time >= record_interval:
        pastime.append(current_time)
        height.append(altitude())
        velocity.append(speed())
        mass_data.append(mass())

        # Вычисляем ускорение
        if len(pastime) > 1:
            time_diff = pastime[-1] - pastime[-2]
            if time_diff > 0:
                accel = (velocity[-1] - velocity[-2]) / time_diff
                acceleration.append(accel)
            else:
                acceleration.append(0)
        else:
            acceleration.append(0)

        last_record_time = current_time

# Функция для сохранения данных в JSON
def save_to_json(filename='flight_data.json'):
    data = {
        "pastime": pastime,
        "height": height,
        "velocity": velocity,
        "acceleration": acceleration,
        "mass": mass_data  # Масса
    }
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# Предстартовая подготовка
vessel.control.sas = False
vessel.control.throttle = 1.0

# Обратный отсчёт и старт
print('3...')
time.sleep(1)
print('2...')
time.sleep(1)
print('1...')
time.sleep(1)
print('Launch!')
vessel.control.activate_next_stage()
vessel.auto_pilot.engage()
vessel.auto_pilot.target_pitch_and_heading(90, 90)

# Основной цикл полёта вверх
srbs_separated = False
turn_angle = 0
while True:
    record_data()
    while True:
        record_data()
        if altitude() > turn_start_altitude and altitude() < turn_end_altitude:
            frac = ((altitude() - turn_start_altitude) / (turn_end_altitude - turn_start_altitude))
            new_turn_angle = frac * 90
            if abs(new_turn_angle - turn_angle) > 0.5:
                turn_angle = new_turn_angle
                vessel.auto_pilot.target_pitch_and_heading(90 - turn_angle, 90)

        if srbs_separated == False:
            if srb_fuel() < 0.1:
                vessel.control.activate_next_stage()
                srbs_separated = True
                print('SRBs separated')
                vessel.control.activate_next_stage()

        if apoapsis() > 180000*0.9: # вывод на периапсис
            vessel.control.throttle = 0.1
            break

    vessel.control.throttle = 0.1
    while apoapsis() < target_altitude:
        record_data()
        pass

    print('Coasting out of atmosphere')
    while altitude() < target_altitude:
        record_data()
        pass

    current_altitude = altitude()
    current_apogee = vessel.orbit.apoapsis
    current_apoapsis = apoapsis()
    if (current_altitude > target_altitude and current_apoapsis < 900000):
        vessel.auto_pilot.engage()
        vessel.auto_pilot.target_pitch_and_heading(-15, 90)

    while (current_altitude > target_altitude and current_apoapsis < 900000):
        vessel.control.throttle = 0.3
        current_apoapsis = apoapsis()

    vessel.control.throttle = 0.0

    time.sleep(5)
    record_data()
    vessel.control.activate_next_stage()
    time.sleep(5)
    record_data()
    vessel.control.activate_next_stage()
    time.sleep(5)
    record_data()
    vessel.control.activate_next_stage()
    time.sleep(5)
    record_data()
    break
print('Elliptical orbit achieved')
save_to_json()
with open('flight_data.json', 'r') as f:
    data = json.load(f)
print("Время (pastime):", data["pastime"])
print("Высота (height):", data["height"])
print("Скорость (velocity):", data["velocity"])
print("Ускорение (acceleration):", data["acceleration"])
print("Масса (mass):", data["mass"])
