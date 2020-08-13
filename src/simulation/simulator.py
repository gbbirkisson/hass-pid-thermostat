import logging
import time

from matplotlib import pyplot as plt

from devices.devices_fake import create_ssr, temp_func
from devices.pid import control_switch

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


def create_simulator(pid):
    return control_switch(pid, create_ssr(), temp_func, sim_stats)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('matplotlib').setLevel(logging.INFO)
    target = 70

    sim = create_simulator(PID(
        2,
        5,
        1,
        setpoint=target,
        output_limits=(0, 5),
        sample_time=8
    ))
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
        if seconds > 1000 + (60 * 50):
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
