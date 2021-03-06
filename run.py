#! .env/bin/python

import multiprocessing
import socket
import http

from burn import surf, log, reg

import config

from db import Guy


if __name__ == '__main__':
    try:
        log('welcome!')

        if 1:
            for g in Guy.objects(level=2):
                reg(g, 2)

        if 0:
            guys = []

            for l in range(3):
                guys.extend(Guy.objects(level=l))

            if config.DEBUG:
                for guy in guys:
                    surf(guy)
            else:
                pool = multiprocessing.Pool(config.THREADS_NUM)
                pool.map_async(surf, guys)
                pool.close()
                pool.join()

    except (socket.error,
            KeyboardInterrupt,
            http.client.RemoteDisconnected) as e:
        log(e, type='error')
        log('bye!')
