import logging
import time

from matplotlib import pyplot as plt

from devices.pid import control_switch
from simulation.thermostat import FakeThermostat

seconds = 1.00


def sec():
    global seconds
    seconds += 0.01
    return seconds


time.monotonic = sec

# Import after time spoof
from simple_pid import PID


def sim_stats(*args):
    pass


def create_simulator(pid, invert):
    thermostat = FakeThermostat(invert=invert)
    return control_switch(pid, thermostat.switch, thermostat.thermometers(), sim_stats)


def heater_simulator(tg):
    return create_simulator(PID(
        2.8,
        0,
        1,
        setpoint=tg,
        sample_time=8,
        output_limits=(0, 5)
    ), False)


def cooler_simulator(tg):
    return create_simulator(PID(
        2,
        0,
        5,
        setpoint=tg,
        sample_time=60,
        output_limits=(-10, 0)
    ), True)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    target = 70
    sim = heater_simulator(target)
    # target = 14
    # sim = cooler_simulator(target)
    x = []
    y = []
    t = []
    on = []
    for temp, on_off in sim:
        x.append(seconds / 60)
        y.append(temp)
        t.append(target)
        on.append(1 if on_off else 0)
        seconds += 1
        if seconds > 1000 + (60 * 45):
            break

    logging.basicConfig(level=logging.ERROR)
    plt.style.use('seaborn')
    fig, ax1 = plt.subplots()
    ax1.plot(x, t, linestyle='dotted')
    ax1.plot(x, y)
    ax1.set_xlabel('minutes')
    ax1.set_ylabel('°C', color='b')
    ax1.legend(['Actual', 'Target'])

    # ax2 = ax1.twinx()
    # ax2.plot(x, on, 'r.')
    # ax2.set_ylabel('on/off', color='r')
    fig.tight_layout()
    fig.savefig('simulation.png', bbox_inches='tight', dpi=300)
