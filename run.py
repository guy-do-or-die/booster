import multiprocessing
import socket
import random
import http
import time

from burn import run, log

import config


if __name__ == '__main__':
    try:
        log('welcome!')
        pool = multiprocessing.Pool(
            initializer=lambda: time.sleep(random.randint(0, 20)))

        pool.map_async(run, config.GUYS)
        pool.close()
        pool.join()
    except (socket.error,
            KeyboardInterrupt,
            http.client.RemoteDisconnected) as e:
        log(e, type='error')
        log('bye!')
