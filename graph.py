import os
from collections import namedtuple

from matplotlib import pyplot as plt
from helpers import now_time

BaseGraphInfo = namedtuple('BaseGraphInfo', ['title', 'type', 'subplots'])
BaseSubGraphInfo = namedtuple('BaseGraphInfo', ['xname', 'yname', 'x', 'y'])


class Graph:

    @staticmethod
    def get_base_graph(base: BaseGraphInfo):
        if not os.path.exists('tmp'):
            os.mkdir('tmp')
        img_path = os.path.join('tmp', f'{base.type}_{now_time()}.png')
        plt.title(base.title)
        plt.figure(figsize=(15, 5 * len(base.subplots)))
        for i, splot in enumerate(base.subplots):
            plt.subplot(len(base.subplots), 1, i+1)
            plt.plot(splot.x, splot.y)
            plt.xlabel(splot.xname, fontsize=14)
            plt.ylabel(splot.yname, fontsize=14)
            plt.grid()
        plt.savefig(img_path)
        plt.close()
        return img_path
