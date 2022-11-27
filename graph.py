import os
from collections import namedtuple
import random

from matplotlib import pyplot as plt
from helpers import now_time

BaseGraphInfo = namedtuple('BaseGraphInfo', ['title', 'type', 'subplots'])
BaseSubGraphInfo = namedtuple('BaseSubGraphInfo', [
    'type', 'linewidth', 'color', 'xname', 'yname', 'x', 'y'
])


class Graph:

    color_map = {
        'blue': 'Blue',
        'aqua': 'Aqua',
        'violet': 'BlueViolet',
        'mint': 'SpringGreen',
        'green': 'ForestGreen',
        'red': 'Crimson',
        'orange': 'OrangeRed',
        'pink': 'DeepPink'
    }

    type_map = {
        'plot': plt.plot,
        'bar': plt.bar
    }

    @staticmethod
    def get_base_graph(base: BaseGraphInfo):
        if not os.path.exists('tmp'):
            os.mkdir('tmp')
        img_path = os.path.join('tmp', f'{base.type}_{now_time()}.png')
        plt.figure(figsize=(15, 5 * len(base.subplots)))
        colors = None
        for i, splot in enumerate(base.subplots):
            if not colors:
                colors = list(Graph.color_map.keys())
            plt.subplot(len(base.subplots), 1, i+1)
            plot = Graph.type_map.get(splot.type, plt.plot)
            random_color = Graph.color_map[colors.pop(random.randint(0, len(colors)-1))]
            plot(splot.x, splot.y, color=splot.color or random_color, linewidth=splot.linewidth)
            plt.title(base.title, size=25) if not i else plt.title('')
            plt.xlabel(splot.xname, fontsize=14)
            plt.ylabel(splot.yname, fontsize=14)
            plt.grid()
        plt.savefig(img_path)
        plt.close()
        return img_path
