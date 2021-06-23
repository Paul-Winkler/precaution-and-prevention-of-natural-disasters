import json
from typing import List
import csv
import numpy as np
import matplotlib.pyplot as plt
from utils import LogProgress, Secure, PyCharmConstants, check_dir

# Festlegen der Konstanten
C = PyCharmConstants


class Evaluation(object):
    population_countries: List[str]
    name = "Evaluation"
    log = None

    @LogProgress()
    def __init__(self):
        self.disaster_types = []
        self.population_countries = []  # Ländernamen, die von der Auswertung der Bevölkerung stammen
        self.types_and_adpy = {}
        self.types_and_adpy_n = {}  # Normiert
        self.types_and_numbers = {}
        self.types_and_deaths = {}
        self.summit_adpy = np.zeros(101)
        self.summit_numbers = np.zeros(101)
        self.disasters_types_in_german = {
            "Earthquake": "Erdbeben", "Drought": "Dürre", "Epidemic": "Epidemie",
            "Flood": "Überflutung", "Storm": "Sturm", "Wildfire": "Waldbrand",
            "Landslide": "Erdrutsch", "Volcanic activity": "Vulkanische Aktivität",
            "Extreme temperature": "Extremtemperatur", "Fog": "Nebel",
            "Mass movement (dry)": "Massenbewegung", "Insect infestation": "Insektenbefall",
            "Impact": "Extraterrestrischer Einschlag", "Animal accident": "Animal accident"
        }

    # Laden der Katastrophentypen- und Länderregister
    @LogProgress()
    def load_registers(self):
        with open(C.DISASTER_TYPE_REGISTER_PATH.value, 'r') as file:
            self.disaster_types = json.load(file)

        with open(C.POPULATION_COUNTRIES_REGISTER_PATH.value, 'r') as file:
            self.population_countries = json.load(file)

    # Erhalten der genauen Dateinamen zum Laden der in den Dateien enthaltenen Werten
    def get_file_name(self, targeted_country) -> str:
        correction = {
            "Azores Islands": "Portugal", "Côte d’Ivoire": "ivoire", "Soviet Union": "Russian Federation",
            "Korea (the Republic of)": "Republic of Korea",
            "Tanzania, United Republic of": "United Republic of Tanzania",
            "Yugoslavia": "Serbia", "Palestine, State of": "State of Palestine",
            "Korea (the Democratic People's Republic of)": "Dem. People's Republic of Korea", "Swaziland": "Eswatini",
            "Virgin Island (U.S.)": "United States Virgin Islands",
            "Virgin Island (British)": "United States Virgin Islands",
            "Macedonia (the former Yugoslav Republic of)": "North Macedonia", "Czech Republic (the)": "Czechia",
            "Moldova (the Republic of)": "Republic of Moldova", "Canary Is": "Spain"
        }

        if targeted_country in correction:
            targeted_country = correction[targeted_country]

        for given_country in self.population_countries:
            if str(targeted_country).lower() in str(given_country).lower():
                return f"{C.POPULATION_FOLDER_PATH.value}/{str(given_country).replace('/', '_').lower()}.json"
            elif str(given_country).lower() in str(targeted_country).lower():
                return f"{C.POPULATION_FOLDER_PATH.value}/{str(given_country).replace('/', '_').lower()}.json"

    # Laden der Bevölkerungsentwicklungen aus den JSON-Dateien
    def get_population(self, targeted_country, year):
        f_name = self.get_file_name(targeted_country)

        with open(f_name, "r") as file:
            data = json.load(file)
            return float(data[str(year)]["count"])

    # Laden der Katastrophentypenentwicklungen aus den JSON-Dateien
    def load_disaster(self, disaster_type):
        with open(f"{C.DEVELOPMENT_OF_DISASTERS_FOLDER_PATH.value}/{str(disaster_type).lower()}.json", 'r') as file:
            return json.load(file)

    # Berechnung der APDY-Entwicklungen sowie Speichern der Häufigkeit und Todesfälle
    @LogProgress()
    def generate_adpy_values(self):
        # Die nachfolgenden Schritte werden für jeden Katastrophentyp ausgeführt
        for d_type in self.disaster_types:
            # Laden der Daten aus dem Zwischengespeicherten JSON-Dateien
            data = self.load_disaster(d_type)

            # Erstellen von Arrays zur Datenspeicherung
            adpys = np.zeros(101)  # ADPY-Werte
            absoulte_numbers = np.zeros(101) # Häufigkeit
            deaths = np.zeros(101)  # Todesfälle

            # Berechnung der ADPY-Werte für jedes Jahr im betrachteten Zeitraum
            for year in range(1920, 2021):
                if str(year) not in data:
                    adpys[year - 1920] = 0
                    continue

                # Berechnung durch Formel 2
                adpn = [
                    np.divide(np.divide(
                        float(data[str(year)][disaster]["deaths"]),
                        self.get_population(
                            str(data[str(year)][disaster]["country"]), year
                        )
                    ), len(data[str(year)]))
                    for disaster in data[str(year)]
                ]

                adpys[year - 1920] = np.sum(adpn)
                deaths[year - 1920] = np.sum([
                    float(data[str(year)][disaster]["deaths"])
                    for disaster in data[str(year)]
                ])
                absoulte_numbers[year - 1920] = len(data[str(year)])

            # Speichern der errechneten Werte
            self.types_and_numbers[d_type] = absoulte_numbers

            self.types_and_deaths[d_type] = deaths

            # Normieren der ADPY-Werte
            self.types_and_adpy[d_type] = adpys
            max_value = np.max(adpys) if np.max(adpys) != 0 else 1
            adpys = np.divide(adpys, max_value)
            self.types_and_adpy_n[d_type] = adpys

    # Zusammenfassen der Daten
    @LogProgress()
    def generate_summit(self):
        for d_type in self.disaster_types:
            self.summit_adpy = np.add(self.summit_adpy, self.types_and_adpy[d_type])
            self.summit_numbers = np.add(self.summit_numbers, self.types_and_numbers[d_type])

        max_value = np.max(self.summit_adpy) if np.max(self.summit_adpy) != 0 else 1
        self.summit_adpy = np.divide(self.summit_adpy, max_value)

    # Erstellen und Sichern der Entwicklungen in den CSV-Dateien
    @LogProgress()
    def generate_and_save_output(self):
        if not check_dir(C.EVALUATION_FOLDER_PATH.value):
            return

        with open(f"{C.EVALUATION_FOLDER_PATH.value}/ADPY-Werte ohne Normierung.csv", 'w+', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')

            writer.writerow(["Jahr"] + [self.disasters_types_in_german[d_type] for d_type in self.disaster_types])
            for i in range(0, 101):
                writer.writerow([str(i + 1920)] + [str(self.types_and_adpy[d_type][i]).replace('.', ',') for d_type
                                                   in self.disaster_types])

        with open(f"{C.EVALUATION_FOLDER_PATH.value}/ADPY-Werte mit Normierung.csv", 'w+', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')

            writer.writerow(["Jahr"] + [self.disasters_types_in_german[d_type] for d_type in self.disaster_types])
            for i in range(0, 101):
                writer.writerow([str(i + 1920)] + [str(self.types_and_adpy_n[d_type][i]).replace('.', ',') for d_type in
                                                   self.disaster_types])

    # Alle Funktionen ab hier dienen nur der graphischen Auswertung

    @LogProgress()
    def plot_all(self):
        standard_color = 'tab:blue'
        times_color = 'tab:red'
        deaths_color = 'k'

        for d_type in self.disaster_types:
            fig, axs = plt.subplots(2, 1, constrained_layout=True)

            for ax in axs.flat:
                ax.set_xlabel('Jahre')
                ax.set_ylabel('ADPY-Werte', color=standard_color)
                ax.grid(True, linestyle='-.')

            axs[0].plot([i for i in range(1920, 2021)], self.types_and_adpy_n[d_type], color=standard_color)
            axs[0].tick_params(axis='y', labelcolor=standard_color)
            axs[0].set_title("Darstellung mit Häufigkeit")

            ax2 = axs[0].twinx()
            ax2.set_ylabel("Häufigkeit pro Jahr", color=times_color)
            ax2.plot([i for i in range(1920, 2021)], self.types_and_numbers[d_type], color=times_color, linewidth=1)
            ax2.tick_params(axis='y', labelcolor=times_color)

            axs[1].plot([i for i in range(1920, 2021)], self.types_and_adpy_n[d_type], color=standard_color)
            axs[1].tick_params(axis='y', labelcolor=standard_color)
            axs[1].set_title("Darstellung mit Todesfällen")

            ax4 = axs[1].twinx()
            ax4.set_ylabel("Todesfälle pro Jahr", color=deaths_color)
            ax4.plot([i for i in range(1920, 2021)], self.types_and_deaths[d_type], color=deaths_color, linewidth=1)
            ax4.tick_params(axis='y', labelcolor=deaths_color)

            fig.tight_layout()

            plt.savefig(f"{C.EVALUATION_FOLDER_PATH.value}/{d_type}.pdf")
            plt.show()

        self.plot("Alle Katastrophen", 'ADPY-Wert', 'Häufigkeit pro Jahr', self.summit_adpy, self.summit_numbers)

    @LogProgress()
    def plot(self, title, y_name1, y_name2, y1, y2):
        fig, ax = plt.subplots()
        ax.set(title=title)

        color = 'tab:blue'
        ax.set_xlabel('Jahre')
        ax.set_ylabel(y_name1, color=color)
        ax.plot([i for i in range(1920, 2021)], y1, color=color)
        ax.tick_params(axis='y', labelcolor=color)
        ax.grid(True, linestyle='-.')

        ax2 = ax.twinx()

        color = 'tab:red'
        ax2.set_ylabel(y_name2, color=color)
        ax2.plot([i for i in range(1920, 2021)], y2, color=color)
        ax2.tick_params(axis='y', labelcolor=color)

        fig.tight_layout()

        plt.savefig(f"{C.EVALUATION_FOLDER_PATH.value}/{title}.pdf")
        plt.show()

    @LogProgress()
    def plot_univariate(self):
        disasters_types_as_array = [
            "Earthquake", "Drought", "Epidemic", "Flood", "Storm", "Wildfire", "Landslide",
            "Volcanic activity", "Extreme temperature", "Fog", "Mass movement (dry)",
            "Insect infestation", "Impact"
        ]

        fig, ax = plt.subplots()
        ax.set_xlabel('Jahre')
        ax.set_ylabel('ADPY-Werte')
        ax.plot([i for i in range(1920, 2021)], self.summit_adpy)
        ax.set_title("Alle Typen")
        ax.grid(True, linestyle='-.')
        plt.savefig(f"{C.EVALUATION_FOLDER_PATH.value}/all_types.pdf")
        plt.show()

        fig, axs = plt.subplots(3, 3, constrained_layout=True)
        for ind, ax in enumerate(axs.flat):
            ax.set_xlabel('Jahre', fontsize=9)
            ax.set_ylabel('ADPY-Werte', fontsize=9)

            d_type = disasters_types_as_array[ind]
            ax.plot([i for i in range(1920, 2021)], self.types_and_adpy_n[d_type], linewidth=1)
            ax.set_title(self.disasters_types_in_german[d_type], fontsize=9)
            ax.grid(True, linestyle='-.')

        plt.savefig(f"{C.EVALUATION_FOLDER_PATH.value}/all_together_part1.pdf")
        plt.show()

        fig, axs = plt.subplots(3, 3, constrained_layout=True)
        for ind, ax in enumerate(axs.flat):
            ax.set_xlabel('Jahre', fontsize=9)
            ax.set_ylabel('ADPY-Werte', fontsize=9)

            d_type = disasters_types_as_array[ind + 9 if ind + 9 <= 12 else 0]
            ax.plot([i for i in range(1920, 2021)], self.types_and_adpy_n[d_type], linewidth=1)
            ax.set_title(self.disasters_types_in_german[d_type], fontsize=9)
            ax.grid(True, linestyle='-.')

        plt.savefig(f"{C.EVALUATION_FOLDER_PATH.value}/all_together_part2.pdf")
        plt.show()

    @LogProgress()
    def plot_variate(self):
        disaster_types_in_variate_plot = [
            "Earthquake", "Drought", "Flood", "Storm", "Wildfire", "Landslide",
            "Volcanic activity", "Extreme temperature", "Mass movement (dry)"
        ]
        fig, axs = plt.subplots(3, 2, constrained_layout=True)
        for ind, ax in enumerate(axs.flat):
            d_type = disaster_types_in_variate_plot[ind]

            color = 'tab:blue'
            ax.set_xlabel('Jahre', fontsize=9)
            ax.set_ylabel("ADPY-Werte", color=color, fontsize=9)
            ax.plot([i for i in range(1920, 2021)], self.types_and_adpy_n[d_type], linewidth=1, color=color)
            ax.tick_params(axis='y', labelcolor=color)
            ax.set_title(self.disasters_types_in_german[d_type], fontsize=9)
            ax.grid(True, linestyle='-.')

            ax2 = ax.twinx()

            color = 'tab:red'
            ax2.set_ylabel("Häufigkeit pro Jahr", color=color, fontsize=9)
            ax2.plot([i for i in range(1920, 2021)], self.types_and_numbers[d_type], color=color, linewidth=1)
            ax2.tick_params(axis='y', labelcolor=color)

            fig.tight_layout()

        plt.savefig(f"{C.EVALUATION_FOLDER_PATH.value}/variate_with_numbers1.pdf")
        plt.show()

        fig, axs = plt.subplots(3, 2, constrained_layout=True)
        for ind, ax in enumerate(axs.flat):
            d_type = disaster_types_in_variate_plot[ind + 6 if ind + 6 < 9 else 0]

            color = 'tab:blue'
            ax.set_xlabel('Jahre', fontsize=9)
            ax.set_ylabel("ADPY-Werte", color=color, fontsize=9)
            ax.plot([i for i in range(1920, 2021)], self.types_and_adpy_n[d_type], linewidth=1, color=color)
            ax.tick_params(axis='y', labelcolor=color)
            ax.set_title(self.disasters_types_in_german[d_type], fontsize=9)
            ax.grid(True, linestyle='-.')

            ax2 = ax.twinx()

            color = 'tab:red'
            ax2.set_ylabel("Häufigkeit pro Jahr", color=color, fontsize=9)
            ax2.plot([i for i in range(1920, 2021)], self.types_and_numbers[d_type], color=color, linewidth=1)
            ax2.tick_params(axis='y', labelcolor=color)

            fig.tight_layout()

        plt.savefig(f"{C.EVALUATION_FOLDER_PATH.value}/variate_with_numbers2.pdf")
        plt.show()

        fig, axs = plt.subplots(3, 2, constrained_layout=True)
        for ind, ax in enumerate(axs.flat):
            d_type = disaster_types_in_variate_plot[ind]

            color = 'tab:blue'
            ax.set_xlabel('Jahre', fontsize=9)
            ax.set_ylabel("ADPY-Werte", color=color, fontsize=9)
            ax.plot([i for i in range(1920, 2021)], self.types_and_adpy_n[d_type], linewidth=1, color=color)
            ax.tick_params(axis='y', labelcolor=color)
            ax.set_title(self.disasters_types_in_german[d_type], fontsize=9)
            ax.grid(True, linestyle='-.')

            ax2 = ax.twinx()

            color = 'k'
            ax2.set_ylabel("Todesfälle pro Jahr", color=color, fontsize=9)
            ax2.plot([i for i in range(1920, 2021)], self.types_and_deaths[d_type], color=color, linewidth=1)
            ax2.tick_params(axis='y', labelcolor=color)

            fig.tight_layout()

        plt.savefig(f"{C.EVALUATION_FOLDER_PATH.value}/variate_with_numbers3.pdf")
        plt.show()

        fig, axs = plt.subplots(3, 2, constrained_layout=True)
        for ind, ax in enumerate(axs.flat):
            d_type = disaster_types_in_variate_plot[ind + 6 if ind + 6 < 9 else 0]

            color = 'tab:blue'
            ax.set_xlabel('Jahre', fontsize=9)
            ax.set_ylabel("ADPY-Werte", color=color, fontsize=9)
            ax.plot([i for i in range(1920, 2021)], self.types_and_adpy_n[d_type], linewidth=1, color=color)
            ax.tick_params(axis='y', labelcolor=color)
            ax.set_title(self.disasters_types_in_german[d_type], fontsize=9)
            ax.grid(True, linestyle='-.')

            ax2 = ax.twinx()

            color = 'k'
            ax2.set_ylabel("Todesfälle pro Jahr", color=color, fontsize=9)
            ax2.plot([i for i in range(1920, 2021)], self.types_and_deaths[d_type], color=color, linewidth=1)
            ax2.tick_params(axis='y', labelcolor=color)

            fig.tight_layout()

        plt.savefig(f"{C.EVALUATION_FOLDER_PATH.value}/variate_with_numbers4.pdf")
        plt.show()


if __name__ == '__main__':
    analytics = Evaluation()
    analytics.load_registers()
    analytics.generate_adpy_values()
    analytics.generate_summit()
    analytics.generate_and_save_output()
    analytics.plot_all()
    analytics.plot_univariate()
    analytics.plot_variate()
