# Импортируем необходимые библиотеки
import krpc  # Библиотека для взаимодействия с Kerbal Space Program
import time  # Библиотека для работы со временем
import math  # Библиотека для математических вычислений

# Устанавливаем соединение с игрой
# name='My project' - идентификатор нашего подключения
conn = krpc.connect(name='My project')

# Получение доступа к важным объектам и функциям
vessel = conn.space_center.active_vessel  # Получаем доступ к активному кораблю
ap = vessel.auto_pilot  # Получаем доступ к автопилоту
control = vessel.control  # Получаем доступ к управлению кораблем
initial_propellant_mass = vessel.mass  # Сохраняем начальную массу корабля с топливом

# Создание потоковых переменных для получения данных в реальном времени
# Эти переменные будут автоматически обновляться при изменении параметров корабля
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')  # Средняя высота над уровнем моря
apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')  # Высота апоапсиса (наивысшая точка орбиты)
periapsis = conn.add_stream(getattr, vessel.orbit, 'periapsis_altitude')  # Высота периапсиса (низшая точка орбиты)
# Получаем вектор скорости относительно поверхности планеты
surface_velocity_stream = conn.add_stream(getattr, vessel.flight(vessel.orbit.body.reference_frame), 'velocity')

# Получение доступа к топливному баку
# Ищем часть корабля с тегом 'rk-7'
fuel_tank = vessel.parts.with_tag('rk-7')[0]

# Получение доступа к ресурсу жидкого топлива в баке
liquid_fuel_resource = fuel_tank.resources.with_resource('LiquidFuel')[0]

# Получение текущего количества топлива
current_fuel = liquid_fuel_resource.amount

# Настройка начальных параметров управления
control.throttle = 1  # Устанавливаем тягу двигателей на максимум
control.sas = True  # Включаем систему стабилизации (SAS)

# Обратный отсчет перед запуском
print("Запуск двигателей прошел успешно, полет через:")
time.sleep(1)
print('3...')
time.sleep(1)
print('2...')
time.sleep(1)
print('1...')
control.activate_next_stage()  # Активируем следующую ступень (запуск двигателей)

# Засекаем время старта
timing = time.time()

# Рассчет идеальной скорости ступенчатой ракеты по формуле Циолковского
total_mass = vessel.mass  # Полная масса корабля
engine_thrust = sum([engine.thrust for engine in vessel.parts.engines])  # Суммарная тяга всех двигателей
specific_impulse = max([engine.specific_impulse for engine in vessel.parts.engines])  # Максимальный удельный импульс
# Расчет идеальной скорости с учетом расхода топлива
ideal_velocity = specific_impulse * 9.81 * vessel.available_thrust / total_mass * math.log((total_mass + vessel.resources.amount("LiquidFuel")) / total_mass)
velocity_origin = ideal_velocity // 10  # Делим на 10 для получения более удобных значений

# Вывод данных на первой минуте полета
print("Данные на 1 минуте \n")
print(f"Идеальная скорость ступенчатой ракеты(суммарная): {velocity_origin} м/с")
print("Время в секундах:", round(time.time() - timing))
print("Расстояние:", altitude(), "км\n")

# Счетчик для отслеживания этапов полета
times = 0
ideal_rocket = 0

# Основной цикл управления полетом
while True:
    # Получаем текущее время полета
    seconds = round(time.time() - timing)

    # Постоянный пересчет идеальной скорости
    total_mass = vessel.mass
    engine_thrust = sum([engine.thrust for engine in vessel.parts.engines])
    specific_impulse = max([engine.specific_impulse for engine in vessel.parts.engines])
    ideal_velocity = specific_impulse * 9.81 * vessel.available_thrust / total_mass * math.log((total_mass + vessel.resources.amount("LiquidFuel")) / total_mass)

    # Расчет текущей скорости относительно поверхности
    surface_velocity = surface_velocity_stream()
    # Вычисляем полную скорость как корень из суммы квадратов компонентов вектора скорости
    surface_speed = surface_velocity[0]**2 + surface_velocity[1]**2 + surface_velocity[2]**2
    surface_speed = surface_speed**0.5
    
    ideal_rocket += ideal_velocity // 10  # Накапливаем идеальную скорость

    # Блок условий для разных этапов полета
    # Вывод данных между 13 и 17 секундами полета
    if 13 <= seconds <= 17:
        if times == 0:
            print(f"Данные на {seconds} минуте \n")
            print(f"Идеальная скорость ступенчатой ракеты(суммарная): {ideal_rocket} м/с")
            print("Расстояние:", altitude(), "км\n")
            times += 1

    # Контроль скорости между 500 и 550 м/с
    if 500 <= surface_speed <= 550:
        if times == 1 and (28 <= seconds <= 32):
            print(f"Данные на {seconds} минуте \n")
            print(f"Идеальная скорость ступенчатой ракеты(суммарная): {ideal_rocket} м/с")
            print("Расстояние:", altitude(), "км\n")
            times += 1
        control.throttle = 0.55  # Уменьшаем тягу для контроля скорости

    # Маневр наклона при достижении определенной высоты
    elif 30000 <= altitude() <= 50000:
        vessel.control.pitch = -1  # Наклоняем ракету вниз
        time.sleep(2.2)  # Ждем 2.2 секунды
        vessel.control.pitch = 0  # Возвращаем в нейтральное положение
    
    # Вывод данных на определенных этапах полета
    elif times == 2 and (58 <= seconds <= 62):
        print(f"Данные на {seconds} минуте \n")
        print(f"Идеальная скорость ступенчатой ракеты(суммарная): {ideal_rocket} м/с")
        print("Расстояние", altitude(), "км\n")
        times += 1
    
    elif (times == 3) and ((88 <= seconds <= 95)):
        print(f"Данные на {seconds} минуте \n")
        print(f"Идеальная скорость ступенчатой ракеты(суммарная): {ideal_rocket} м/с")
        print("Расстояние:", altitude(), "км\n")
        times += 1

    # Стабилизация на определенной высоте
    elif 50500 <= altitude() <= 60000:
        vessel.control.pitch = 0  # Выравниваем ракету
        control.sas = True  # Включаем систему стабилизации

    # Условие для завершения первого этапа полета
    elif altitude() >= 60500 or current_fuel < 7:
        break

# Отделение ступени и подготовка к орбитальному полету
print("Выход в космос прошел успешно!")
control.activate_next_stage()  # Активируем следующую ступень

# Корректировка положения для орбитального полета
control.sas = True  # Включаем систему стабилизации
vessel.control.pitch = -1  # Наклоняем ракету
time.sleep(4.8)  # Ждем 4.8 секунды
vessel.control.pitch = 0  # Возвращаем в нейтральное положение

print("Ракета идет к орбите")

# Ожидание достижения целевых параметров орбиты
while True:
    # Проверяем, достигли ли мы нужных значений апоапсиса и периапсиса
    if (930000 <= apoapsis() <= 970000) and (120000 <= periapsis() <= 150000):
        break
    else:
        pass

# Финальная корректировка положения
control.sas = False
vessel.control.pitch = 0.05  # Небольшой наклон вверх
time.sleep(0.5)
vessel.control.pitch = 0  # Возврат в нейтральное положение
control.sas = True  # Включаем систему стабилизации
control.throttle = 0  # Выключаем двигатели

# Выпуск спутника на орбиту
time.sleep(5)  # Ждем 5 секунд
control.activate_next_stage()  # Активируем следующую ступень
time.sleep(5)  # Ждем еще 5 секунд
control.activate_next_stage()  # Активируем финальную ступень
time.sleep(5)  # Ждем 5 секунд
control.antennas = True  # Активируем антенны

print("Спутник успешно вышел на орбиту!")