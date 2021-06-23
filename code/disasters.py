import json
from utils import LogProgress, Secure, PyCharmConstants, CSVReader, check_dir


# Festlegen der Konstanten
C = PyCharmConstants


class DisasterDataConverter(CSVReader):
    name = "DisasterDataConverter"
    log = None

    @LogProgress()
    def __init__(self):
        super().__init__(C.EMDAT_DISASTERS_DATA_PATH.value, ';')
        self.disasters = []
        self.countries = []

    # Auswerten der aus der Datei bezogenen Daten
    @Secure("data")
    @LogProgress()
    def convert_data(self):
        for row in self.data:
            ident = str(row[0])
            continent = str(row[13])
            country = str(row[10])
            iso = str(row[11])
            year = str(row[1])
            d_group = str(row[3])
            d_subgroup = str(row[4])
            d_type = str(row[5])
            d_subtype = str(row[6])
            deaths = int(str(row[34])) if str(row[34]) != '' else 0
            entry_criteria = str(row[9])

            if country not in self.countries:
                self.countries.append(country)

            if d_type in self.converted_data:
                if year in self.converted_data[d_type]:
                    self.converted_data[d_type][year][ident] = {"continent": continent, "country": country, "iso": iso, "group": d_group, "subgroup": d_subgroup, "type": d_type, "subtype": d_subtype, "deaths": deaths, "entry": entry_criteria}
                else:
                    self.converted_data[d_type][year] = {ident: {"continent": continent, "country": country, "iso": iso, "group": d_group, "subgroup": d_subgroup, "type": d_type, "subtype": d_subtype, "deaths": deaths, "entry": entry_criteria}}
            else:
                self.converted_data[d_type] = {year: {ident: {"continent": continent, "country": country, "iso": iso, "group": d_group, "subgroup": d_subgroup, "type": d_type, "subtype": d_subtype, "deaths": deaths, "entry": entry_criteria}}}

    # Extrahieren der Katastrophentypen
    @Secure("converted_data")
    @LogProgress()
    def extract_disasters(self):
        for d_type in self.converted_data:
            self.disasters.append(d_type)

    # Sichern der Daten in JSON-Dateien
    @Secure("converted_data")
    @LogProgress()
    def write_data(self):
        if not check_dir(C.DEVELOPMENT_OF_DISASTERS_FOLDER_PATH.value):
            return

        with open(f"{C.DEVELOPMENT_OF_DISASTERS_FOLDER_PATH.value}/all_disasters.json", 'w+') as file:
            json.dump(self.converted_data, file)

        with open(C.DISASTER_COUNTRIES_REGISTER_PATH.value, 'w+') as file:
            json.dump(self.countries, file)

        with open(C.DISASTER_TYPE_REGISTER_PATH.value, 'w+') as file:
            json.dump(self.disasters, file)

        for d_type in self.converted_data:
            loc = str(d_type).replace('/', '_').lower()
            with open(f"{C.DEVELOPMENT_OF_DISASTERS_FOLDER_PATH.value}/{loc}.json", 'w+') as file:
                json.dump(self.converted_data[d_type], file)


# Prozess und Ablauf der Analyse
if __name__ == '__main__':
    converter = DisasterDataConverter()
    converter.get_data_from_file()
    converter.convert_data()
    converter.extract_disasters()
    converter.write_data()
