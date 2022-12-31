import requests
from xml.etree import ElementTree
from pprint import pprint
import tomllib
import re

import xmltodict as xmltodict

from datetime import datetime
import openai


class WeatherAPI:

    def __init__(self):
        with open('config.toml', 'rb') as configfile:
            self.config = tomllib.load(configfile)

        with open('names-all-cities.csv', 'r') as file:
            self.cities = {line.rstrip() for line in file if len(line) > 3}

        openai.api_key = self.config['openapi']['apikey']

    def startup(self):
        print('Welcome to weather chatbot. \n'
              'Note: This program can only search for the weather forecast for the next 5 days.')

        while True:
            forecast_prompt = input("\n\nWould you like to know? \n")  # Example: 'What is the weather in London on 2nd of January?'
            forecast_prompt = re.sub(r'[^\w\s]', '', forecast_prompt).lower()

            city_prompt = ''

            # print(forecast_prompt)
            for word in self.cities:
                if word in forecast_prompt and len(word) > len(city_prompt):
                    city_prompt = word


            if city_prompt == '':
                print("ERROR: City / Location can't be found")
                continue

            question = self.__weather_query(city_prompt, forecast_prompt)
            # print(question)

            response = self.__get_response(question)
            print(response)





    def __weather_query(self, city_prompt: str, forecast_prompt: str) -> str:
        # weather_url = f"{BASE_URL}weather?q={location}&appid={API_Key}&units={UNITS}"
        weather_url = f"{self.config['openweather']['base_url']}forecast?q={city_prompt}&appid={self.config['openweather']['apikey']}&units={self.config['openweather']['units']}"

        weather_data = requests.get(weather_url).json()
        # pprint(weather_data)

        question_start = f"The following is the weather forcast for {weather_data['city']['name']}:"
        question_newinfo = [question_start]

        for index, this in enumerate(weather_data['list']):
            if index % 3:
                continue

            question_newinfo.append(
                f"At {this['dt_txt']}:\n"
                f"- Weather is {this['weather'][0]['description']}.\n"
                f"- Temperature is {this['main']['temp']} celsius.\n"
                f"- Pressure is {this['main']['pressure']} hPa.\n"
                f"- Humidity is {this['main']['humidity']}%.\n"
                f"- Wind speed is {this['wind']['speed']} m/s."
            )

        return '\n\n'.join(question_newinfo) \
            + f"\n\nToday's date and time is {datetime.today().strftime('%Y-%m-%d %H:%M:%S')} \n\nAs a chatbot, {forecast_prompt}\n\n"


    def __get_response(self, question: str) -> str:
        response = openai.Completion.create(
            model=self.config['openapi']['model'],
            prompt=question,
            temperature=self.config['openapi']['temperature'],
            max_tokens=self.config['openapi']['max_tokens']
        )
        # print(response)

        match response['choices'][0]['finish_reason']:
            case 'stop':
                return response['choices'][0]['text']
            case _:
                print("Error - didn't finish")
                return response['choices'][0]['text']



### XML
# response = requests.get(weather_url)
# tree = ElementTree.fromstring(response.content)
#
# toprint = ElementTree.tostring(tree, encoding='unicode', method='xml')
# print(response.content.decode("utf-8"))


weatherapi = WeatherAPI()
weatherapi.startup()
