import os
from collections import namedtuple
import random

from matplotlib import pyplot as plt
from helpers import now_time
from exceptions import TBotException

BaseGraphInfo = namedtuple('BaseGraphInfo', ['title', 'type', 'subplots'])


class BaseSubGraphInfo:

    class Param:
        def __init__(self, name: str, required: bool = False):
            if not name:
                raise TBotException(code=6, message=f'name is empty')
            self.name = name
            self.required = required

    attributes = [
        Param('type', True),
        Param('color'),
        Param('xname', True),
        Param('yname', True),
        Param('x', True),
        Param('y', True)
    ]

    def __init__(self, **kwargs):
        """
        Base array of parameters for graph generation
        :param type: type of line
        :param color: not required color of line
        """
        for kw in kwargs.keys():
            if kw not in [attrib.name for attrib in BaseSubGraphInfo.attributes]:
                raise TBotException(code=6, message=f'Unknown param "{kw}" = {kwargs[kw]}')
        for attrib in BaseSubGraphInfo.attributes:
            if attrib.name not in kwargs.keys():
                if attrib.required:
                    raise TBotException(code=6, message=f'Param {attrib.name} is required')
                exec(f"self.{attrib.name} = None")
            else:
                if isinstance(kwargs.get(attrib.name, None), str):
                    kwargs[attrib.name] = f"'{kwargs.get(attrib.name, None)}'"
                exec(f"self.{attrib.name} = {kwargs.get(attrib.name, None)}")


class Graph:

    color_map = {
        'blue': 'Blue',
        'aqua': 'Aqua',
        'violet': 'BleViolet',
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

    line_colors = 'rgbcmykw'

    @staticmethod
    def get_base_graph(base: BaseGraphInfo):
        if not os.path.exists('tmp'):
            os.mkdir('tmp')
        img_path = os.path.join('tmp', f'{base.type}_{now_time()}.png')
        plt.title(base.title)
        plt.figure(figsize=(15, 5 * len(base.subplots)))
        colors = None
        for i, splot in enumerate(base.subplots):
            if not colors:
                colors = list(Graph.line_colors)
            plt.subplot(len(base.subplots), 1, i+1)
            plot = Graph.type_map.get(splot.type, plt.plot)
            plot(splot.x, splot.y, color=splot.color or colors.pop(random.randint(0, len(colors)-1)))
            plt.xlabel(splot.xname, fontsize=14)
            plt.ylabel(splot.yname, fontsize=14)
            plt.grid()
        plt.savefig(img_path)
        plt.close()
        return img_path
