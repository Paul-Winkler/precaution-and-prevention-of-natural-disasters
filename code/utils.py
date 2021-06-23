from enum import Enum
import csv
import os


# Konstanten
class PyCharmConstants(Enum):
    UN_POPULATION_DATA_PATH = "./../resources/WPP2019_total_population.csv"
    EMDAT_DISASTERS_DATA_PATH = "./../resources/emdat_public_2020_10_03_1920-2020.csv"
    POPULATION_COUNTRIES_REGISTER_PATH = "./../resources/population_development_of_each_country/countries.json"
    DISASTER_COUNTRIES_REGISTER_PATH = "./../resources/development_of_disaster_for_each_disaster/countries.json"
    DISASTER_TYPE_REGISTER_PATH = "./../resources/development_of_disaster_for_each_disaster/disasters.json"

    POPULATION_FOLDER_PATH = "./../resources/population_development_of_each_country"
    POPULATION_CHARTS_FOLDER_PATH = "./../resources/population_charts"
    DEVELOPMENT_OF_DISASTERS_FOLDER_PATH = "./../resources/development_of_disaster_for_each_disaster"
    EVALUATION_FOLDER_PATH = "./../resources/evaluation_results"


# Dekoratoren
class LogProgress(object):
    """
    Includes function in PROGRESS logging and creates a function specific log lambda,
    which can be called in the function.

    It accepts no arguments.
    """

    def __init__(self):
        self.loc = ""

    def __call__(self, f):
        def wrapped_f(wrapped_self, *args):
            self.generate_location(f, wrapped_self)
            self.generate_class_log(wrapped_self)

            self.generate_class_log(wrapped_self)
            basic_log(f"Starting {self.loc}", log_type="PROGRESS")
            f(wrapped_self, *args)
            basic_log(f"Finishing {self.loc}", log_type="PROGRESS")

        return wrapped_f

    def generate_location(self, f, wrapped_self):
        self.loc = f"{f.__name__} in {wrapped_self.name}"

    def generate_class_log(self, wrapped_self):
        wrapped_self.log = lambda text, log_type="INFO": basic_log(text, log_type, log_location=self.loc)


class Secure(object):
    """
    Checks if parent class contains specific values before the function is executed.
    If it doesn't or the value is None/Empty the security cancels the function call to prohibit an exception.

    It takes all value which should be checked as arguments: Secure(*args)
    """

    def __init__(self, *args):
        self.args = args

    def __call__(self, f):
        def wrapped_f(wrapped_self, *args):
            for arg in self.args:
                if not (hasattr(wrapped_self, arg) and getattr(wrapped_self, arg) is not None and bool(getattr(wrapped_self, arg))):
                    wrapped_self.log(f"Canceled {f.__name__} due to missing property {arg}", log_type="SECURITY")
                    return

            f(wrapped_self, *args)

        return wrapped_f


# Funktionen
def basic_log(text, log_type="INFO", log_location=None):
    """
    Function for standardized logging
    :param text: String to log
    :param log_type: Type
    :param log_location: Location of caller
    :return: nothing
    """

    if log_location is None:
        print("[{}]: {}".format(log_type, text))
    else:
        print("[{}] -> {}: {}".format(log_type, log_location, text))


def check_dir(path):
    """
    Checks if a directory exits
    :param path:
    :return: False if a directory could not be created, True if it exits or was successful created
    """
    if not os.path.exists(path):
        try:
            os.mkdir(path)
        except OSError:
            print("Could not create dir, path: ", path)
            return False

    return True


# CSV Reader Superklasse
class CSVReader(object):
    """
    Basic CSVReader.
    Extracts csv data from file and safes it in attributes data and converted_data.
    """
    name = "CSVReader"
    log = None

    @LogProgress()
    def __init__(self, file_path, delimiter):
        self.delimiter = delimiter
        self.csv_file = None
        self.data = []
        self.converted_data = {}

        try:
            self.file = open(file_path, "r")
        except FileNotFoundError:
            self.log("Datei nicht gefunden", log_type="ERROR")

    @Secure("file")
    @LogProgress()
    def get_data_from_file(self):
        self.csv_file = csv.reader(self.file, delimiter=self.delimiter)

        for row in self.csv_file:
            row_list = []

            for element in row:
                row_list.append(element)

            self.data.append(row_list)

        self.log("Alle Daten aus der Datei ausgelesen")
        self.file.close()