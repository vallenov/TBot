import os
from collections import namedtuple

from matplotlib import pyplot as plt
from helpers import now_time

BaseGraphInfo = namedtuple('BaseGraphInfo', ['type', 'xname', 'yname', 'x', 'y'])


class Graph:

    @staticmethod
    def get_base_graph(base: BaseGraphInfo):
        if not os.path.exists('tmp'):
            os.mkdir('tmp')
        img_path = os.path.join('tmp', f'{base.type}_{now_time()}.png')
        plt.figure(figsize=(15, 5))
        plt.plot(base.x, base.y)
        plt.xlabel(base.xname, fontsize=14)
        plt.ylabel(base.yname, fontsize=14)
        plt.grid()
        plt.savefig(img_path)
        plt.close()
        return img_path
