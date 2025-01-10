import numpy as np  # Библиотека для работы с массивами и научными вычислениями
from scipy.integrate import odeint  # Функция для численного решения ОДУ (метод интеграции)
import matplotlib.pyplot as plt  # Библиотека для построения графиков
import statistics  # Библиотека для некоторых статистических функций (в данном коде не используется явно)

# --- Константы и исходные данные --- #

G_global = 6.67430e-11  # Гравитационная постоянная (Н*м^2/кг^2)
R_global = 600000  # Радиус планеты (м). Для KSP (Kerbin) радиус меньше, чем у Земли.
M_global = 5.2915158e22  # Масса планеты (кг)
g_earth = 9.81  # Ускорение свободного падения у поверхности (м/с^2), приблизительно
d_rocket = 5.14  # Диаметр ракеты (м)
S_rocket = np.pi * (d_rocket ** 2) / 4.0  # Площадь поперечного сечения ракеты (м^2), тоже не используется непосредственно

# Орбитальная высота и скорость (эти переменные для информации, в коде не используются напрямую)
orbitH = 80000  # Высота орбиты (м), для справки
orbitV = np.sqrt(G_global * M_global / (R_global + orbitH))  # Орбитальная скорость на высоте orbitH по формуле круговой орбиты

# Начальная масса ракеты
startMass = 53000  # кг

# --- Параметры ступеней (время работы, массы, расходы топлива) --- #

# Временные промежутки работы ступеней (в секундах):
t0_burn = 23.7  # Время работы бустеров (совместно с первой ступенью)
t1_burn = 58.4  # Далее время работы первой ступени
t2_burn = 74.3  # Время работы второй ступени
t3_burn = 307.7  # Время работы третьей ступени
# Общее время после выключения бустеров (не обязательно используется прямо)
T_all = t1_burn + t2_burn + t3_burn

# Массовые расходы топлива (omega), кг/с:
w_boosters = 118.71  # Бустеры
w_stage1 = 68.51  # 1-я ступень
w_stage2 = 17.73  # 2-я ступень
w_stage3 = 0.65  # 3-я ступень

# Полная и сухая масса бустеров
boosterMass_total = 3.8 * 1000  # Полная масса бустеров вместе с топливом (кг)
boosterMassFuel = 2813  # Масса топлива в бустерах (кг)
boosterMassDry = boosterMass_total - boosterMassFuel  # Сухая масса (без топлива)

# Полная и сухая масса 1-й ступени
stage1Mass_total = 10.63 * 1000
stage1MassFuel = 4000
stage1MassDry = stage1Mass_total - stage1MassFuel

# Полная и сухая масса 2-й ступени
stage2Mass_total = 1.86 * 1000
stage2MassFuel = 1300
stage2MassDry = stage2Mass_total - stage2MassFuel

# Полная и сухая масса 3-й ступени
stage3Mass_total = 0.7 * 1000
stage3MassFuel = 200
stage3MassDry = stage3Mass_total - stage3MassFuel

# --- Загрузка данных из файлов KSP (время, высота, скорость, масса) --- #
# Предполагается, что файлы Time.txt, Hight.txt, Speed.txt, Mass.txt находятся в одной папке.
# В этих файлах данные перечислены через запятую, например: "0, 1, 2, 3, ...".

with open("Time.txt", encoding="UTF-8") as file_in:
    kspTime_raw = (file_in.read()).split(', ')

with open("Hight.txt", encoding="UTF-8") as file_in:
    kspHeight = [float(x) for x in (file_in.read()).split(', ')]

with open("Speed.txt", encoding="UTF-8") as file_in:
    kspSpeed = [float(x) for x in (file_in.read()).split(', ')]

with open("Mass.txt", encoding="UTF-8") as file_in:
    kspMass = [float(x) for x in (file_in.read()).split(', ')]

# Здесь мы создаём массив kspTime, идущий по единичным шагам,
# равным длине массива kspTime_raw. Это упрощённый подход
# (вместо фактического времени из файла просто 0,1,2,...).
kspTime = []
c_counter = 0
for i in range(len(kspTime_raw)):
    kspTime.append(c_counter)
    c_counter += 1


# --- Функция для расчёта текущей массы ракеты во времени --- #
def getMass(t):
    """
    Возвращает массу ракеты в момент времени t.
    Учтены:
    - Одновременная работа бустеров и 1-й ступени в интервале [0, t0_burn].
    - Сбрасывание бустеров после выработки их топлива (после t0_burn).
    - Работа 1-й ступени до t1_burn.
    - Сбрасывание 1-й ступени после t1_burn.
    - Работа 2-й ступени до (t1_burn + t2_burn).
    - Сбрасывание 2-й ступени после (t1_burn + t2_burn).
    - Работа 3-й ступени до (t1_burn + t2_burn + t3_burn).
    - После t1_burn + t2_burn + t3_burn топлива нет, остаётся только сухая масса.
    """
    # Если t < 0, ещё не начался отсчёт. Возвращаем стартовую массу
    if t < 0:
        return startMass

    # 1) Пока t <= t0_burn, работают бустеры и 1-я ступень вместе
    if t <= t0_burn:
        return startMass - w_boosters * t - w_stage1 * t

    # Считаем массу после сброса бустеров (вычитаем их топливо и сухую массу)
    massAfterBoosters = startMass - boosterMassFuel - boosterMassDry

    # 2) Далее, пока t <= t1_burn, работает только 1-я ступень
    if t <= t1_burn:
        return massAfterBoosters - w_stage1 * t

    # Масса после отработки 1-й ступени (минус её топливо и сухую массу)
    massAfterStage1 = massAfterBoosters - stage1MassFuel - stage1MassDry

    # 3) Пока t <= (t1_burn + t2_burn), работает 2-я ступень
    if t <= t2_burn + t1_burn:
        dt = t - t1_burn  # время работы 2-й ступени (после отделения 1-й ступени)
        return massAfterStage1 - w_stage2 * dt

    # Масса после сброса 2-й ступени
    massAfterStage2 = massAfterStage1 - stage2MassFuel - stage2MassDry

    # 4) Пока t <= (t1_burn + t2_burn + t3_burn), работает 3-я ступень
    if t2_burn + t1_burn < t <= t1_burn + t2_burn + t3_burn:
        dt = t - t2_burn - t1_burn  # время работы 3-й ступени (после отделения 2-й)
        return massAfterStage2 - w_stage3 * dt

    # После (t1_burn + t2_burn + t3_burn) топлива нет, остаётся только сухая масса 3-й ступени
    return massAfterStage2 - stage3MassDry


# --- Функция для расчёта суммарного массового расхода топлива во времени --- #
def getOmega(t):
    """
    Возвращает, сколько килограммов топлива в секунду (кг/с) тратится
    в момент времени t (суммарно для всех работающих ступеней).
    """
    if 0 <= t <= t0_burn:
        # Когда работают и бустеры, и 1-я ступень одновременно
        return w_boosters + w_stage1
    elif t0_burn < t <= t1_burn:
        # Когда работают только 1-я ступень
        return w_stage1
    elif t1_burn < t <= t1_burn + t2_burn:
        # Когда работает только 2-я ступень
        return w_stage2
    elif t1_burn + t2_burn < t <= t1_burn + t2_burn + t3_burn:
        # Когда работает только 3-я ступень
        return w_stage3
    else:
        # После окончания работы всех ступеней - 0
        return 0.0


# --- Функция для расчёта коэффициента (или удельной тяги) q(t) --- #
def getQ(t):
    """
    Возвращает некий коэффициент 'Q' (Ньютоны на (кг/с) или нечто подобное),
    который далее умножается на массовый расход w = omega(t) для получения силы тяги F_thrust.

    F_thrust = w * Q
    """
    if 0 <= t <= t0_burn:
        # Во время работы бустеров + 1-й ступени
        return 1667.1 + 2451
    elif t0_burn < t <= t1_burn:
        return 3138.1
    elif t1_burn < t <= t2_burn + t1_burn:
        return 3383.3
    elif t2_burn + t1_burn < t <= t2_burn + t1_burn + t3_burn:
        return 3089.1
    else:
        return 0.0


# --- Функция для расчёта угла наклона тяги во времени alpha(t) --- #
def getAlpha(t):
    """
    Возвращает угол наклона вектора тяги (в радианах).
    Здесь взята простая экспоненциальная функция:
        alpha(t) = (pi/2) * exp(-t / 53)
    Это значит, что сначала угол близок к pi/2 (90 градусов, вертикально),
    а затем с ростом времени угол уменьшается (ракета "наклоняется").
    """
    return (np.pi / 2) * np.exp(-t / 53)


# --- Функция для расчёта локального g (ускорения свободного падения) на высоте y --- #
def localG(y):
    """
    Возвращает локальное ускорение свободного падения
    по формуле гравитации: g = G * M / (R + y)^2,
    где R + y - расстояние от центра планеты.
    """
    return G_global * M_global / (R_global + y) ** 2


# --- Главная функция, задающая правые части ОДУ (системы дифференциальных уравнений) --- #
def equations(stateVec, t):
    """
    Функция, используемая в odeint для расчёта производных dx/dt, dy/dt, dvx/dt, dvy/dt.

    Вектор stateVec = [x, y, vx, vy]:
        x  - горизонтальная координата (м)
        y  - вертикальная координата (м) (высота)
        vx - скорость по оси x (м/с)
        vy - скорость по оси y (м/с)

    t  - текущее время (с)

    Возвращает список [dx/dt, dy/dt, dvx/dt, dvy/dt].
    """
    xCoor, yCoor, vxCoor, vyCoor = stateVec  # Распаковка координат и скоростей

    # Текущая масса ракеты
    currentMass = getMass(t)
    # Если масса вдруг меньше 1 кг, подстрахуемся, чтобы не было деления на 0
    if currentMass < 1.0:
        currentMass = 1.0

    # Угол наклона тяги
    alphaVal = getAlpha(t)
    # Локальное g (зависит от высоты y)
    gLocal = localG(yCoor)
    # Массовый расход топлива (кг/с)
    massFlow = getOmega(t)
    # Коэффициент тяги (или удельный импульс в Н/(кг/с))
    Qvalue = getQ(t)

    # Полная тяга (Н)
    Fthrust = 3 * massFlow * Qvalue

    # Горизонтальные и вертикальные компоненты тяги
    FthrustX = Fthrust * np.cos(alphaVal)
    FthrustY = Fthrust * np.sin(alphaVal)

    # Уравнения движения по осям:
    # dx/dt = vx
    dxDt = vxCoor

    # dy/dt = vy (но только если угол > 0.06 рад, иначе ставим vy=0 для упрощения)
    if alphaVal > 0.06:
        dyDt = vyCoor
    else:
        dyDt = 0

    # dvx/dt = (F_thrust_x) / mass
    dvxDt = FthrustX / currentMass

    # dvy/dt = (F_thrust_y) / mass - g_local (только если угол > 0.06)
    if alphaVal > 0.06:
        dvyDt = (FthrustY / currentMass) - gLocal
    else:
        dvyDt = 0

    return [dxDt, dyDt, dvxDt, dvyDt]


# --- Точка входа: основная программа --- #
if __name__ == '__main__':
    # Начальные условия для системы ОДУ:
    # x=0, y=0, vx=0, vy=0
    Xinit = [0.0, 0.0, 0.0, 0.0]

    # Конечное время моделирования (с). Можно менять при необходимости.
    tEnd = 234.0
    # Массив временных точек от 0 до tEnd, всего 234 точек (по 1 с между точками)
    tGrid = np.linspace(0, tEnd, 234)

    # Решаем систему ОДУ методом odeint:
    #    dX/dt = equations(X, t), начальные условия Xinit, на сетке tGrid
    solution = odeint(equations, Xinit, tGrid)

    # Распаковываем результат (в каждом столбце массива solution хранится x, y, vx, vy)
    solX = solution[:, 0]  # Координата x во времени
    solY = solution[:, 1]  # Координата y (высота) во времени
    solVx = solution[:, 2]  # Скорость по x
    solVy = solution[:, 3]  # Скорость по y

    # Считаем массу ракеты, угол альфа, локальное g и модуль скорости в те же моменты времени
    solMass = np.array([getMass(ti) for ti in tGrid])  # Масса
    solAlpha = np.array([getAlpha(ti) for ti in tGrid])  # Угол тяги
    solG = np.array([localG(ti) for ti in tGrid])
    # ВАЖНО: здесь есть нюанс:
    # gravity(ti) вызвано с аргументом ti, который является временем, а не высотой.
    # На самом деле, чтобы построить "g от времени" правильно, нужно было бы использовать gravity(y_sol[i]).
    # Но код оставлен, как есть, для иллюстрации.

    solVel = np.sqrt(solVx ** 2 + solVy ** 2)  # Полный модуль скорости (м/с)

    # solOmega - массив значений массового расхода топлива во времени
    solOmega = np.array([getOmega(ti) for ti in tGrid])

    # Обрезаем данные KSP до 234 точек, чтобы сравнить с результатами модели
    kspSpeed = kspSpeed[:234]
    kspMass = kspMass[:234]
    kspHeight = kspHeight[:234]

    # Средние отклонения между моделью и KSP (по модулю разности, усреднённо)
    # 1) Отклонение массы
    devMass = (
            sum([abs(kspMass[i] - solMass[i]) for i in range(len(kspMass))]) /
            len([abs(kspMass[i] - solMass[i]) for i in range(len(kspMass))])
    )

    # 2) Отклонение скорости
    devSpeed = (
            sum([abs(kspSpeed[i] - solVel[i]) for i in range(len(kspSpeed))]) /
            len([abs(kspSpeed[i] - solVel[i]) for i in range(len(kspSpeed))])
    )

    # 3) Отклонение высоты
    devHeight = (
            sum([abs(kspHeight[i] - solY[i]) for i in range(len(kspHeight))]) /
            len([abs(kspHeight[i] - solY[i]) for i in range(len(kspHeight))])
    )

    # Выводим полученные средние отклонения
    print(f'{round(devMass, 3)} - среднее отклонение массы')
    print(f'{round(devHeight, 3)} - среднее отклонение высоты')
    print(f'{round(devSpeed, 3)} - среднее отклонение скорости')

    # --- Построение графиков --- #
    fig, axs = plt.subplots(3, 3, figsize=(12, 10))

    # График скорости от времени
    axs[0][0].plot(tGrid, kspSpeed, color='r', label='ksp')
    axs[0][0].plot(tGrid, solVel, label='model')
    axs[0][0].set_xlabel("t, c")
    axs[0][0].set_ylabel("Скорость, м/с")
    axs[0][0].grid(True)
    axs[0][0].set_title("График скорости от времени")
    axs[0][0].legend()

    # График массы от времени
    axs[0][1].plot(tGrid, kspMass, color='r', label='ksp')
    axs[0][1].plot(tGrid, solMass, label='model')
    axs[0][1].set_xlabel("t, c")
    axs[0][1].set_ylabel("Масса, кг")
    axs[0][1].grid(True)
    axs[0][1].set_title("График массы от времени")
    axs[0][1].legend()

    # График высоты от времени
    axs[1][0].plot(tGrid, kspHeight, color='r', label='ksp')
    axs[1][0].plot(tGrid, solY, label='model')
    axs[1][0].set_xlabel("t, c")
    axs[1][0].set_ylabel("Высота, м")
    axs[1][0].grid(True)
    axs[1][0].set_title("График высоты от времени")
    axs[1][0].legend()

    # Траектория движения в координатной плоскости (x, y)
    axs[1][1].plot(solX, solY)
    axs[1][1].set_xlabel("x, м")
    axs[1][1].set_ylabel("y, м")
    axs[1][1].grid(True)
    axs[1][1].set_title("Перемещение в координатной плоскости")

    # Скорость по x
    axs[2][1].plot(tGrid, solVx)
    axs[2][1].set_xlabel("t, c")
    axs[2][1].set_ylabel("Vx, м/c")
    axs[2][1].grid(True)
    axs[2][1].set_title("Скорость по x")

    # Скорость по y
    axs[2][0].plot(tGrid, solVy)
    axs[2][0].set_xlabel("t, c")
    axs[2][0].set_ylabel("Vy, м/c")
    axs[2][0].grid(True)
    axs[2][0].set_title("Скорость по y")

    # График изменения угла альфа (в радианах) от времени
    axs[1][2].plot(tGrid, solAlpha)
    axs[1][2].set_xlabel("t, c")
    axs[1][2].set_ylabel("Угол, рад")
    axs[1][2].grid(True)
    axs[1][2].set_title("График угла от времени")

    # График g(ti) (но на самом деле ti - время, а не высота!)
    # В идеале: g_sol = [gravity(y_sol[i]) for i in range(len(t_points))]
    axs[0][2].plot(tGrid, solG)
    axs[0][2].set_xlabel("t, c")
    axs[0][2].set_ylabel("Ускорение, м/с^2")
    axs[0][2].grid(True)
    axs[0][2].set_title("График ускорения свободного падения (упрощённо)")

    # График омеги (массового расхода топлива) во времени
    axs[2][2].plot(tGrid, solOmega)
    axs[2][2].set_xlabel("t, c")
    axs[2][2].set_ylabel("Омега, кг/с")
    axs[2][2].grid(True)
    axs[2][2].set_title("График омеги от времени")

    # Подгонка отступов между графиками и вывод
    plt.tight_layout()
    plt.show()
