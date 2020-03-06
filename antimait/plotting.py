"""
Plotting utilities for incoming data based on matplotlib.pyplot.
"""

import matplotlib.pyplot as plt  # type: ignore
from typing import List, Dict, Union
from pathlib import Path
import datetime
import logging

from . import DataReceiver, Comm

__all__ = ["Plotter"]


class Plotter(DataReceiver):
    """
    Plotter class, this is a wrapper for matplotlib.pyplot and for a structure containing the
    sensor data.
    """

    _PLOTTING_PERIOD = 10  # every 10 new elements

    def __init__(self, session_name: str, frequency_mode: bool = None,
                 data: Union[List[float], Dict[str, int]] = None,
                 overwrite: bool = None, img_dir: str = None):
        """

        Args:
            session_name: the name of the session that will be used as the plot file name
            frequency_mode: if set to true, data is collected as a dict where data[elem] => frequency_elem
            data: data already available, used to initialize the Plotter obj instead of an empty collection
            overwrite: if True the plot image will be just one and will always be owerwritten
            img_dir: if specified, images will be saved in this dir instead of Path.cwd()
        """

        self._session_name = session_name
        self._frequency_mode = frequency_mode or False
        self._session_data = data or [] if not self._frequency_mode else {}
        self._overwrite = True if overwrite is None else overwrite
        self._elem_counter: int = 0

        if img_dir:
            img_path = Path(img_dir)
            if not img_path.exists():
                raise ValueError("{} is not a correct path".format(img_dir))
            self._img_dir = img_path.absolute()
        else:
            self._img_dir = Path.cwd().absolute()

    def update(self, action: Comm, **update: str) -> None:
        if action == Comm.DATA:
            if "data" in update:
                data: Union[str, float] = update["data"]
                if not self._frequency_mode:
                    try:
                        data = float(data)
                    except ValueError:
                        logging.warning("Parsing error form float to str")
                        return
                self.add(data)
            else:
                logging.error("data keyword not passed!")
        elif action == Comm.CLOSING:
            self.plot()
            logging.info("Plotter {} closing!".format(self._session_name))

    def add(self, elem: Union[float, str]) -> None:
        """
        Adds an element or a list of elements to the internal data that is being plotted.
        Args:
            elem: the element to add, either a float or a list of floats

        Returns:
            None
        """

        if self._frequency_mode:
            if isinstance(self._session_data, dict) and isinstance(elem, str):
                if elem not in self._session_data:
                    self._session_data[elem] = 1
                else:
                    self._session_data[elem] += 1
        else:
            if isinstance(self._session_data, list) and isinstance(elem, float):
                self._session_data.append(elem)

        self._elem_counter += 1

        if self._elem_counter == self._PLOTTING_PERIOD:
            self.plot()
            self._elem_counter = 0

    def clear(self):
        """
        Just a wrapper around list.clear()

        Returns:
            None
        """

        self._session_data.clear()

    def plot(self) -> Path:
        """
        Plots the contents of session_data using matplotlib.pyplot.
        This method generates an image for the plotted data in the directory specified in __init__.
        Returns:
            pathlib.Path, the absolute Path of the generated plot
        """
        file_name: str
        plt.title(self._session_name)
        if self._frequency_mode:
            if isinstance(self._session_data, dict):
                plt.bar(self._session_data.keys(), self._session_data.values())
        else:
            plt.plot(self._session_data)

        if not self._overwrite:
            date_fmt = datetime.datetime.now().strftime("%d-%m-%y_%I-%M-%S")
            file_name = "{}_{}".format(self._session_name, date_fmt)
        else:
            file_name = self._session_name

        plt.savefig(Path(self._img_dir, file_name))
        plt.clf()
        return Path(self._img_dir, file_name, ".png")
