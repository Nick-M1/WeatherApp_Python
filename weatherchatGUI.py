import io
import tkinter as tk
from PIL import Image, ImageTk
import requests
import tomllib
import re
from datetime import datetime
import openai



# CONSTANTS
BG_GRAY = "#ABB2B9"
BG_COLOR = "#17202A"
TEXT_COLOR = "#EAECEE"
FONT = "Helvetica 14"
FONT_BOLD = "Helvetica 13 bold"

SCREENWIDTH = 80
BASEWIDTH = 300                 # Image width in chatbox


class WeatherApp:

    def __init__(self):

        # TKINTER SET-UP:
        self.root = tk.Tk()
        self.root.title("Chatbot")

        self.root.configure(background='black', width=SCREENWIDTH)

        tk.Label(self.root, bg=BG_COLOR, fg=TEXT_COLOR, text="Welcome", font=FONT_BOLD, padx=10, pady=10, width=20, height=1) \
            .grid(row=0)

        self.txt = tk.Text(self.root, bg=BG_COLOR, fg=TEXT_COLOR, font=FONT, width=SCREENWIDTH, wrap=tk.WORD)
        self.txt.grid(row=1, column=0, columnspan=2)

        self.txt.tag_config('startup', foreground="gray80")
        self.txt.tag_config('warning', foreground="red")
        self.txt.tag_config('user', foreground="aquamarine")
        self.txt.tag_config('bot', foreground="violet")

        # scrollbar = tk.Scrollbar(self.txt)
        # scrollbar.place(relheight=1, relx=0.974)

        self.e = tk.Entry(self.root, bg="#2C3E50", fg=TEXT_COLOR, font=FONT, width=72)
        self.e.grid(row=2, column=0)

        tk.Button(self.root, text="Send", font=FONT_BOLD, bg=BG_GRAY, command=self.__run) \
            .grid(row=2, column=1)



        self.txt.insert(
            tk.END,
            'Welcome to weather chatbot. Please enter your questions\n'
            '(NOTE: Can only search for the weather forecast for the next 5 days)\n',
            'startup'
        )
        self.txt.insert(tk.END, "\n\nBot ->  What would you like to know? :)", 'bot')


        # OTHER SET-UP:
        with open('config.toml', 'rb') as configfile:
            self.config = tomllib.load(configfile)

        with open('names-all-cities.csv', 'r') as file:
            self.cities = {line.rstrip() for line in file if len(line) > 3}

        openai.api_key = self.config['openapi']['apikey']


    # On-enter function
    def __run(self):
        user_input = self.e.get()
        self.txt.insert(tk.END, f'\nYou ->  {user_input}', 'user')

        # Clean the user's input (all lower case and punctuation removed)
        forecast_prompt = re.sub(r'[^\w\s]', '', user_input).lower()

        # Find the city name in user input string
        city_prompt = ''
        for word in self.cities:
            if word in forecast_prompt and len(word) > len(city_prompt):
                city_prompt = word

        if city_prompt == '':
            self.txt.insert(tk.END, "\nError: City / Location can't be found", 'warning')
            self.txt.insert(tk.END, "\n\n\nBot ->  What would you like to know? :)", 'bot')
            return

        question = self.__weather_query(city_prompt, forecast_prompt)
        response = self.__get_response(question)

        self.txt.insert(tk.END, f"\nBot ->  {response}\n", 'bot')

        img = self.__create_image(f'Nice scenic, beautiful, landscape picture of {response}')
        self.__append_image(img)

        self.txt.insert(tk.END, "\n\n\nBot ->  What would you like to know? :)", 'bot')
        self.e.delete(0, tk.END)


    def __weather_query(self, city_prompt: str, forecast_prompt: str) -> str:
        weather_url = f"{self.config['openweather']['base_url']}forecast?q={city_prompt}&appid={self.config['openweather']['apikey']}&units={self.config['openweather']['units']}"
        weather_data = requests.get(weather_url).json()

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

        match response['choices'][0]['finish_reason']:
            case 'stop':
                return response['choices'][0]['text']
            case _:
                print("Error - didn't finish")
                return response['choices'][0]['text']


    def __create_image(self, prompt: str):
        resultJSON = openai.Image.create(
            prompt=prompt,
            n=self.config['openapi']['image_num'],
            size=self.config['openapi']['image_size']
        )

        response = requests.get(resultJSON['data'][0]['url'], stream=True)
        image = Image.open(io.BytesIO(response.content))
        return image

    def __append_image(self, img) -> None:
        # Add next image and save a reference to it
        global imgToInsert

        wpercent = (BASEWIDTH / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((BASEWIDTH, hsize), Image.Resampling.LANCZOS)  # Resize the image in the given width

        imgToInsert = ImageTk.PhotoImage(img)  # Convert the image in TkImage

        label_imgs = tk.Label(image=imgToInsert)
        label_imgs.image = imgToInsert  # keep a reference!

        self.txt.image_create(tk.END, image=imgToInsert)


    def mainloop(self) -> None:
        self.root.mainloop()



if __name__ == "__main__":
  app = WeatherApp()
  app.mainloop()
