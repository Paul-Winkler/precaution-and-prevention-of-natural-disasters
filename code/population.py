import json
import numpy as np
import matplotlib.pyplot as plt
from utils import LogProgress, Secure, PyCharmConstants, CSVReader, check_dir


# Festlegen der Konstanten
C = PyCharmConstants


class PopulationDataConverter(CSVReader):
    name = "PopulationDataConverter"
    log = None

    @LogProgress()
    def __init__(self):
        super().__init__(C.UN_POPULATION_DATA_PATH.value, ',')

        self.countries = []

    # Auswerten der aus der Datei bezogenen Daten
    @Secure("data")
    @LogProgress()
    def convert_data(self):
        for row in self.data:
            country = row[1]
            year = row[4]
            count = int(str(row[8]).replace('.', ''))
            if len(str(row[8]).split('.')) != 2:
                count *= 10 ** 3
            elif len(str(row[8]).split('.')[1]) - 3 != 0:
                count *= 10 ** (3 - len(str(row[8]).split('.')[1]))

            density = float(str(row[9]))

            if int(year) > 2020:
                continue

            if country in self.converted_data:
                self.converted_data[country][year] = {"count": count, "density": density}
            else:
                self.converted_data[country] = {year: {"count": count, "density": density}}

    # Extrahieren der Länder zum Erstellen einer Liste
    @Secure("converted_data")
    @LogProgress()
    def extract_countries(self):
        for country in self.converted_data:
            self.countries.append(country)

    # Berechnen der ungefähren Bevölkerungszahlen vor 1950
    @Secure("converted_data")
    @LogProgress()
    def calculate_missing_population_numbers(self):
        # Für jedes aus den Daten ausgelesene Land erfolgen diese Schritte
        for country in self.converted_data:
            years = []
            for year in ["1950", "1951", "1952", "1953", "1954", "1955"]:
                years.append(self.converted_data[country][year])

            # Erstellen von Matrizen zum Speichern der Werte
            real_numbers = np.zeros((2, 5))
            comparison_numbers = np.zeros((2, 5))

            # Zuordnen der Werte zu den richtigen Matrizen
            for ind, year in enumerate(years):
                if ind < 5:
                    real_numbers[0, ind] = year["count"]
                    real_numbers[1, ind] = year["density"]
                if ind > 0:
                    comparison_numbers[0, ind - 1] = year["count"]
                    comparison_numbers[1, ind - 1] = year["density"]

            # Berechnen der Veränderung
            divided = np.divide(comparison_numbers, real_numbers)

            growth_avg = float(np.average(divided[0, :]))
            density_avg = float(np.average(real_numbers[1, :]))

            new_years = [str(year) for year in range(1920, 1950)]
            new_years.reverse()

            # Kalkulation der Jahre 1920 bis 1950 und speichern der Werte
            population = self.converted_data[country]["1950"]["count"]
            density = self.converted_data[country]["1950"]["density"]
            for year in new_years:
                population = int((population / growth_avg))
                density = int((density / density_avg))
                self.converted_data[country][year] = {
                    "count": population,
                    "density": density
                }

    # Sortieren Daten nach Jahreszahlen
    @Secure("converted_data")
    @LogProgress()
    def sort_data(self):
        for country in self.converted_data:
            local_copy = {}
            for y in range(1920, 2021):
                local_copy[str(y)] = self.converted_data[country][str(y)]
            self.converted_data[country] = local_copy

    # Sichern der Daten im lokalen Speicher
    @Secure("converted_data")
    @LogProgress()
    def calculate_development(self):
        for country in self.converted_data:
            development = []
            for year in self.converted_data[country]:
                development.append(self.converted_data[country][year]["count"])

            self.converted_data[country]["development"] = development

    # Sichern der Daten in Form von JSON-Dateien
    @Secure("converted_data")
    @LogProgress()
    def write_data(self):
        if not check_dir(C.POPULATION_FOLDER_PATH.value):
            return

        with open(C.POPULATION_COUNTRIES_REGISTER_PATH.value, 'w+') as file:
            json.dump(self.countries, file)

        for country in self.converted_data:
            loc = str(country).replace('/', '_').replace(':', ' ').lower()
            with open(f"{C.POPULATION_FOLDER_PATH.value}/{loc}.json", 'w+') as file:
                json.dump(self.converted_data[country], file)

    # Erstellen der graphischen Auswertung
    @Secure("converted_data")
    @LogProgress()
    def plot(self):
        if not check_dir(C.POPULATION_CHARTS_FOLDER_PATH.value):
            return

        for country in self.converted_data:
            fig, ax = plt.subplots()

            ax.set_xlabel('Jahre')
            ax.set_ylabel('Menschen')
            ax.set_title('Veränderung der Bevölkerung - ' + country)

            values = self.converted_data[country]['development']
            ax.plot([i for i in range(1920, 2021)], values)

            fname = str(country).replace('/', '_').replace(':', ' ').lower()
            fig.savefig(f"{C.POPULATION_CHARTS_FOLDER_PATH.value}/{fname}.pdf")

            plt.close(fig)


# Prozess und Ablauf der Analyse
if __name__ == '__main__':
    converter = PopulationDataConverter()
    converter.get_data_from_file()
    converter.convert_data()
    converter.extract_countries()
    converter.calculate_missing_population_numbers()
    converter.sort_data()
    converter.calculate_development()
    converter.write_data()
    converter.plot()
