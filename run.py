#! .env/bin/python

import multiprocessing
import socket
import http

from burn import run, log

import config


if __name__ == '__main__':
    try:
        log('welcome!')

        if config.DEBUG:
            for g in config.GUYS:
                run(g)
        else:
            pool = multiprocessing.Pool(config.THREADS_NUM)
            pool.map_async(run, config.GUYS)
            pool.close()
            pool.join()
    except (socket.error,
            KeyboardInterrupt,
            http.client.RemoteDisconnected) as e:
        log(e, type='error')
        log('bye!')
