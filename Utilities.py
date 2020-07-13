from flask_googletrans import translator
from flask import Flask, render_template
from shutil import copy2, copytree, rmtree, make_archive, move
import json
import os
import zipfile


class Utils:

    local_path = os.getcwd()
    config_path = "{0}\\{1}".format(local_path, "config.json")
    translator = None
    config = None
    language = 'es'

    def batch_translation(self, array, special_characters=None):
        texts = self.config['line_separator'].join(array)
        translated_texts = self.translate(texts, special_characters)
        translated_array = translated_texts.split(self.config['line_separator'])
        return translated_array

    @staticmethod
    def unzip(path, file, directory_to_extract_to='assets'):
        with zipfile.ZipFile('{0}\\{1}'.format(path, file), 'r') as zip_ref:
            zip_ref.extractall(directory_to_extract_to)

    @staticmethod
    def zip(path, output_filename='assets'):
        print("Zipping {1} file into path: {0}".format(path, output_filename))
        make_archive("{0}\\{1}".format(path, output_filename), 'zip', "{0}\\{1}".format(path, 'assets'))

    @staticmethod
    def remove_special_values(text, open_symbol='<', closing_symbol='>'):
        """
        Remove the special values used by the game before translating the text, e.i. <PLAYER>, <BLANK>
        :param text: Text to skip
        :param open_symbol: Symbol representing the start of the special value
        :param closing_symbol: Symbol representing the end of the special value
        :return: Dictionary [(bool) was the special value found, text with values removed, array of values]
        """
        aux_array = []
        aux_string = ''
        clean_text = ''
        found = False

        for x in range(0, len(text)):
            if text[x] == open_symbol:
                found = True
                clean_text += open_symbol
            elif text[x] == closing_symbol:
                # if the closing symbol was found store the word on the array
                aux_array.append(aux_string)
                aux_string = ''
                clean_text += closing_symbol
                found = False
            elif found:
                aux_string += text[x]
            else:
                clean_text += text[x]

        result = {
                   "was_value_found": len(clean_text) != len(text),
                   "clean_text": clean_text,
                   "array_of_values": aux_array
                }

        return result

    @staticmethod
    def add_back_special_values(text, array, open_symbol='<'):
        full_text = ''
        index = 0
        for x in range(0, len(text)):
            if text[x] == open_symbol:
                if index < len(array):
                    full_text += open_symbol + array[index]
                else:
                    full_text += open_symbol
                index += 1
            else:
                full_text += text[x]
        return full_text

    def translate(self, text, special_characters=None, src='en'):

        if not text or str.isspace(text):
            return ""
        if text.lower() in self.config['localization_skip_words']:
            return text

        dict_special_values = {}

        if special_characters is None:
            special_characters = [['<', '>']]

        clean_text = text

        for characters in special_characters:
            dict_special_values[characters[0]] = self.remove_special_values(clean_text,
                                                                            open_symbol=characters[0],
                                                                            closing_symbol=characters[1])
            clean_text = dict_special_values[characters[0]]['clean_text']
        translated_text = self.translator.translate(clean_text, src=src, dest=['{0}'.format(self.language)])

        final_text = translated_text
        for key in dict_special_values.keys():
            if dict_special_values[key]['was_value_found']:
                final_text = self.add_back_special_values(translated_text,
                                                          dict_special_values[key]
                                                          ['array_of_values'],
                                                          open_symbol=key)
        return final_text

    @staticmethod
    def read_json(input_json, encoding='utf-8'):
        with open(input_json, "r", encoding=encoding) as read_file:
            return json.load(read_file)

    @staticmethod
    def write_json(data, path, file, encoding='utf-8'):
        if not os.path.exists(path):
            os.makedirs(path)
        with open("{0}/{1}".format(path, file), 'w+', encoding=encoding) as fp:
            json.dump(data, fp, ensure_ascii=False)

    @staticmethod
    def copy(input_file, output_directory):
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        copy2(input_file, output_directory)

    @staticmethod
    def copy_directory(input_directory, output_directory):
        copytree(input_directory, output_directory)

    def refresh_output(self, input_path, output_path):
        if os.path.exists(output_path) and os.path.isdir(output_path):
            rmtree(output_path, ignore_errors=True)
        self.copy_directory(input_path, output_path)

    @staticmethod
    def remove_file(path, file_name):
        file_path = '{0}\\{1}'.format(path, file_name)

        if os.path.exists(file_path):
            os.remove(file_path)
            print('File removed: {0}'.format(file_path))
        else:
            print('File not found: {0}'.format(file_path))

    @staticmethod
    def format_file(file_name, input_path=os.getcwd(), output_path=None):

        to_format = '.bin' if file_name[-4:] == '.zip' else '.zip'
        zip_code = b'PK\x03\x04\n\x00\x00\x00\x08\x00f\xafJ'
        bin_code = b'JBGP\n\x00\x00\x00\x08\x00f\xafJ'

        if output_path is None:
            output_path = input_path

        if os.path.isfile('{0}{1}'.format(file_name[:-4], to_format)):
            os.rename('{0}\\{1}'.format(output_path, '{0}{1}'.format(file_name[:-4], to_format)),
                      '{0}\\{1}'.format(output_path, '{0}{1}{2}'.format(file_name[:-4], to_format, '_bck'))
                      )
            print("File {0} already exists in path {2}, has been rename to {1}".format(file_name, '{0}{1}'.format(file_name, '_bck'), output_path))

        with open('{0}\\{1}'.format(input_path, file_name), 'rb') as f:
            content = f.read()
            no_code = content[13:]
            if to_format == '.bin':
                coded = b''.join([bin_code, no_code])
            else:
                coded = b''.join([zip_code, no_code])
            output_file = open('{0}\\{1}{2}'.format(output_path, file_name[:-4], to_format), 'wb')
            output_file.write(coded)
            print("File created successfully: {0}".format(output_file))
            output_file.close()

    def create_config(self, default_config):
        if os.path.isfile(self.config_path):
            config = Utils.read_json(self.config_path)
            print("Config found")
        else:
            default_config['input_path'] = self.local_path
            default_config['output_path'] = "{0}\\{1}\\".format(self.local_path, "output")
            config = default_config
            Utils.write_json(default_config, self.local_path, "config.json")
            print("Config created")
        self.config = config
        return config

    def set_language(self, language):
        self.language = language

    def unzip_assets(self, config, file_name='assets'):
        if not os.path.exists('{0}\\{1}'.format(config['input_path'], file_name)):
            if os.path.isfile('{0}\\{1}'.format(config['input_path'], '{0}.zip'.format(file_name))):
                self.unzip(config['input_path'], 'assets.zip')
            else:
                print("Error: assets.zip file not found on input_path.")
                exit(-1)

    def zip_assets(self, config, file_name='assets'):
        if not os.path.exists('{0}\\{1}'.format(config['input_path'], file_name)):
            if os.path.isfile('{0}\\{1}'.format(config['input_path'], '{0}.zip'.format(file_name))):
                self.zip(config['input_path'])
            else:
                print("Error: assets.zip file not found on input_path.")
                exit(-1)

    def translate_menus(self, config, game, special_characters=None):

        input_menu_path = "{0}\\{1}\\".format(config['input_path'], config['games'][game]['path'])
        output_menu_path = "{0}\\{1}\\".format(config['output_path'], config['games'][game]['path'])

        localization = self.read_json('{0}\\{1}'.format(input_menu_path, 'Localization.json'))
        amount_of_files = len(localization['table']['en'])
        index = 0

        for line in localization['table']['en']:
            index += 1
            if isinstance(localization['table']['en'][line], list):
                # If the current object is a list, translate the list values
                for i in range(0, len(localization['table']['en'][line])):
                    localization['table']['en'][line][i] = self.translate(localization['table']['en'][line][i], special_characters=special_characters)
            else:
                if line in config['localization_forced_ins'].keys():
                    localization['table']['en'][line] = config['localization_forced_ins'][line]
                else:
                    localization['table']['en'][line] = self.translate(localization['table']['en'][line], special_characters=special_characters)

            print("Translating in-game Menu ({1}%): {0}".format(line, int((index / amount_of_files) * 100)))
        self.write_json(localization, '{0}'.format(output_menu_path), 'Localization.json')

    def __init__(self):
        app = Flask(__name__)
        self.translator = translator(app)
