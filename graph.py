import os
import datetime

from matplotlib import pyplot as plt


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
        unique_name = str(datetime.datetime.now()).replace(':', '').replace(' ', '')[:16]
        img_path = os.path.join('tmp', f'graph_{unique_name}.png')
        plt.figure(figsize=(15, 5))
        plt.plot(dates, count_of_queries)
        plt.xlabel('Date', fontsize=14)
        plt.ylabel('Count of requests', fontsize=14)
        plt.grid()
        plt.savefig(img_path)
        plt.close()
        return img_path
