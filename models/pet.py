import json
import random
import os
from io import BytesIO
from datetime import datetime
from collections import deque

from PIL import Image

from utils import gemini_client

class Pet:
    def __init__(self, name, health, hunger, emotion, chat_history=None, image_number=None, last_fed_time=None,last_play_time=None,last_chat_time=None):
        self.name = name
        self.health = health
        self.hunger = hunger
        self.emotion = emotion
        self.status = []
        self.animal_type, self.characteristics = self.get_animal_and_characteristics()
        self.image = image_number if image_number is not None else self.generate_image()
        self.prompt = self.generate_prompt()
        self.chat_history = chat_history if chat_history is not None else ""
        self.last_fed_time = last_fed_time if last_fed_time is not None else datetime.now()
        self.last_play_time = last_play_time if last_play_time is not None else datetime.now()
        self.last_chat_time = last_chat_time if last_chat_time is not None else datetime.now()

    def get_animal_and_characteristics(self):
        with open('utils/data/animal_types.json', encoding='utf-8') as f:
            animals = json.load(f)['Portuguese']
        with open('utils/data/personality_traits.json', encoding='utf-8') as f:
            characteristics = json.load(f)['Portuguese']

        animal_type = random.choice(animals)
        char_1, char_2, char_3 = random.sample(characteristics, 3)
        
        return animal_type, [char_1, char_2, char_3]

    def generate_image(self):
        prompt = (
            f"a 16 bit sprite-sheet like a tamagochi of a {self.animal_type} face with 6 frames "
            "and black background"
        )
        image_bytes = gemini_client.generate_image(prompt)

        image = Image.open(BytesIO(image_bytes))
        next_file_number = self.get_pet_number("assets/pet_animations")
        image.save(f"assets/pet_animations/pet_{next_file_number}.png")

        self.generate_atlas_file(next_file_number)

        return next_file_number
    
    def generate_atlas_file(self, image_number: int):
        image_path = os.path.abspath(f"assets/pet_animations/pet_{image_number}.png")

        with Image.open(image_path).convert("L") as grayscale:
            width, height = grayscale.size
            pixels = grayscale.load()
            mask = [[pixels[x, y] > 20 for x in range(width)] for y in range(height)]

        visited = [[False] * width for _ in range(height)]
        components = []
        for y in range(height):
            for x in range(width):
                if not mask[y][x] or visited[y][x]:
                    continue
                queue = deque([(x, y)])
                visited[y][x] = True
                min_x = max_x = x
                min_y = max_y = y
                pixel_count = 0
                while queue:
                    cx, cy = queue.popleft()
                    pixel_count += 1
                    if cx < min_x:
                        min_x = cx
                    if cx > max_x:
                        max_x = cx
                    if cy < min_y:
                        min_y = cy
                    if cy > max_y:
                        max_y = cy
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < width and 0 <= ny < height and mask[ny][nx] and not visited[ny][nx]:
                            visited[ny][nx] = True
                            queue.append((nx, ny))

                component_width = max_x - min_x + 1
                component_height = max_y - min_y + 1
                bounding_area = component_width * component_height
                if 25000 < bounding_area < 230000:
                    atlas_y = height - (min_y + component_height)
                    components.append(
                        {
                            "x": min_x,
                            "y": atlas_y,
                            "w": component_width,
                            "h": component_height,
                        }
                    )

        components.sort(key=lambda item: item["x"])

        data_dict = {image_path: {}}
        for idx, comp in enumerate(components, start=1):
            data_dict[image_path][f"frame{idx}"] = [comp["x"], comp["y"], comp["w"], comp["h"]]

        # Gera o caminho do arquivo de saída
        output_file = "utils/data/animation_mapping.atlas"

        # Escreve o dicionário como um arquivo JSON
        with open(output_file, 'w') as f:
            json.dump(data_dict, f, indent=4)


    def get_pet_number(self, directory_path):
        files = os.listdir(directory_path)
        max_number = 0
        for file in files:
            # Apenas considera arquivos que começam com "pet_" e terminam com ".png"
            if file.startswith("pet_") and file.endswith(".png"):
                try:
                    number = int(file.replace("pet_", "").replace(".png", ""))
                    if number > max_number:
                        max_number = number
                except ValueError:
                    # Ignora arquivos que não seguem o formato esperado
                    continue
        return max_number + 1
    
    def generate_prompt(self):
        return (f"Você é um pet virtual como um tamagochi seu nome é {self.name}. "
                f"Você é do tipo {self.animal_type} eu tenho a responsabilidade de cuidar de você. "
                f"Suas características são {self.characteristics[0]}, {self.characteristics[1]} e também bastante {self.characteristics[2]}. "
                f"Atue com um pet virtual de acordo com essas características.")

    def update_pet_status(self):
        current_time = datetime.now()

        last_fed_time_datetime = datetime.strptime(self.last_fed_time, "%Y-%m-%dT%H:%M:%S.%f") if isinstance(self.last_fed_time, str) else self.last_fed_time
        last_play_time_datetime = datetime.strptime(self.last_play_time, "%Y-%m-%dT%H:%M:%S.%f") if isinstance(self.last_play_time, str) else self.last_play_time
        last_chat_time_datetime = datetime.strptime(self.last_chat_time, "%Y-%m-%dT%H:%M:%S.%f") if isinstance(self.last_chat_time, str) else self.last_chat_time
        time_diference = current_time - last_fed_time_datetime
        time_diference = time_diference.total_seconds() /60
        self.hunger += int(time_diference)*10
        self.hunger = min(self.hunger,100)

        if self.hunger > 11:
            self.health -=int(time_diference /10) *10
            self.health = max(self.health, 0)

        if self.hunger > 11:
            if 'Faminto' not in self.status:
                self.status.append('Faminto')
        else:
            if 'Faminto' in self.status:
                self.status.remove('Faminto')

        if self.health > 70:
            if 'Saudavel' not in self.status:
                self.status.append('Saudavel')
        else:
            if 'Saudavel' in self.status:
                self.status.remove('Saudavel')

        if self.hunger == 0:
            if 'Nao querendo comer' not in self.status:
                self.status.append('Nao querendo comer')
        else:
            if 'Nao querendo comer' in self.status:
                self.status.remove('Nao querendo comer')

        if self.health < 50:
            if 'Doente' not in self.status:
                self.status.append('Doente')
            if (current_time - last_fed_time_datetime).total_seconds() > 48*60*60:  # Se passou mais de 48 horas
                if 'Morto' not in self.status:
                    self.status.append('Morto')
        else:
            if 'Doente' in self.status:
                self.status.remove('Doente')

        if (current_time - last_play_time_datetime).total_seconds() > 4*60*60:  # Se passou mais de 4 horas
            if 'Entediado' not in self.status:
                self.status.append('Entediado')
        else:
            if 'Entediado' in self.status:
                self.status.remove('Entediado')

        if (current_time - last_chat_time_datetime).total_seconds() > 4*60*60:  # Se passou mais de 4 horas
            if 'Triste' not in self.status:
                self.status.append('Triste')
        else:
            if 'Triste' in self.status:
                self.status.remove('Triste')

    def feed(self):
        self.hunger = max(0, self.hunger - 10)
        self.last_fed_time = datetime.now()
        self.update_pet_status()
        self.save_info()

    def give_injection(self):
        self.health = min(100, self.health + 10)
        self.save_info()

    def play(self):
        self.last_play_time = datetime.now()
        self.update_pet_status()
        self.save_info()
    
    def generate_reaction(self, action):
        reaction_prompt = (
            self.chat_history
            + f"Como um {self.animal_type}, quando voce esta {self.status} "
            f"diga uma frase para quando o meu dono {action}. Responda de forma {self.characteristics[0]}"
        )

        reaction = gemini_client.generate_text(reaction_prompt)
        self.chat_history += f"Seu pet reagiu: {reaction}\n"
        self.save_info(self.chat_history)
        return reaction

    def save_info(self, chat_history=None):
        if chat_history is None:
            chat_history = self.chat_history
        pet_info = {
            'name': self.name,
            'animal_type': self.animal_type,
            'characteristics': self.characteristics,
            'health': self.health,
            'hunger': self.hunger,
            'emotion': self.emotion,
            'status': self.status,
            'image_number': self.image,  
            'last_fed_time':self.last_fed_time.isoformat() if isinstance(self.last_fed_time, datetime) else self.last_fed_time,
            'last_play_time': self.last_play_time.isoformat() if isinstance(self.last_play_time, datetime) else self.last_play_time,
            'last_chat_time': self.last_chat_time.isoformat() if isinstance(self.last_chat_time, datetime) else self.last_chat_time,
            "chat_history": chat_history
        }
        with open('save_file.txt', 'w') as file:
            json.dump(pet_info, file)

    def get_image_path(self):
        return f'assets/pet_animations/pet_{self.image}.png'

    def get_prompt(self):
        return self.prompt
