import os

from matplotlib import pyplot as plt
from helpers import now_time


class Graph:

    @staticmethod
    def get_statistic_graph(dates: list, count_of_queries: list) -> str:
        """
        Create graph image
        :param dates: list of dates
        :param count_of_queries: list of counts
        :return: path to image
        """
        if not os.path.exists('tmp'):
            os.mkdir('tmp')
        img_path = os.path.join('tmp', f'graph_{now_time()}.png')
        plt.figure(figsize=(15, 5))
        plt.plot(dates, count_of_queries)
        plt.xlabel('Date', fontsize=14)
        plt.ylabel('Count of requests', fontsize=14)
        plt.grid()
        plt.savefig(img_path)
        plt.close()
        return img_path

    @staticmethod
    def get_weather_graph(dates: list, temperature: list):
        if not os.path.exists('tmp'):
            os.mkdir('tmp')
        img_path = os.path.join('tmp', f'weather_{now_time()}.png')
        plt.figure(figsize=(15, 5))
        plt.plot(dates, temperature)
        plt.xlabel('Date', fontsize=14)
        plt.ylabel('Temperature (°C)', fontsize=14)
        plt.grid()
        plt.savefig(img_path)
        plt.close()
        return img_path
