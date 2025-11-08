import json
import random
import os
from io import BytesIO
from datetime import datetime
from collections import deque

from PIL import Image

from utils import gemini_client


LEGACY_STATUS_TRANSLATIONS = {
    'Faminto': 'Hungry',
    'Saudavel': 'Healthy',
    'Doente': 'Sick',
    'Entediado': 'Bored',
    'Triste': 'Sad',
    'Morto': 'Deceased',
    'Nao querendo comer': 'Full',
}

LEGACY_CHAT_REPLACEMENTS = {
    'Seu pet reagiu:': 'Your pet reacted:',
    'O peixe é eficiente. Repõe o que faltava e garante a energia para nadar e estar pronto para o próximo mergulho.': 'Fish is efficient. It replenishes what was missing and keeps you energized to swim and be ready for the next dive.',
}

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
            animals = json.load(f)['English']
        with open('utils/data/personality_traits.json', encoding='utf-8') as f:
            characteristics = json.load(f)['English']

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

        # Output atlas file path
        output_file = "utils/data/animation_mapping.atlas"

        # Write atlas data to disk as JSON for the animation player
        with open(output_file, 'w') as f:
            json.dump(data_dict, f, indent=4)


    def get_pet_number(self, directory_path):
        files = os.listdir(directory_path)
        max_number = 0
        for file in files:
            # Only consider files that match the generated pet sprite naming convention
            if file.startswith("pet_") and file.endswith(".png"):
                try:
                    number = int(file.replace("pet_", "").replace(".png", ""))
                    if number > max_number:
                        max_number = number
                except ValueError:
                    # Skip files that do not follow the expected naming pattern
                    continue
        return max_number + 1
    
    def generate_prompt(self):
        return (
            f"You are a virtual pet similar to a Tamagotchi and your name is {self.name}. "
            f"You are a {self.animal_type} and I am responsible for taking care of you. "
            f"Your personality traits are {self.characteristics[0]}, {self.characteristics[1]}, and {self.characteristics[2]}. "
            f"Role-play as a virtual pet that embodies those traits."
        )

    def update_pet_status(self):
        self.status = self.normalize_statuses(self.status)
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
            if 'Hungry' not in self.status:
                self.status.append('Hungry')
        else:
            if 'Hungry' in self.status:
                self.status.remove('Hungry')

        if self.health > 70:
            if 'Healthy' not in self.status:
                self.status.append('Healthy')
        else:
            if 'Healthy' in self.status:
                self.status.remove('Healthy')

        if self.hunger == 0:
            if 'Full' not in self.status:
                self.status.append('Full')
        else:
            if 'Full' in self.status:
                self.status.remove('Full')

        if self.health < 50:
            if 'Sick' not in self.status:
                self.status.append('Sick')
            if (current_time - last_fed_time_datetime).total_seconds() > 48*60*60:  # More than 48 hours without food
                if 'Deceased' not in self.status:
                    self.status.append('Deceased')
        else:
            if 'Sick' in self.status:
                self.status.remove('Sick')

        if (current_time - last_play_time_datetime).total_seconds() > 4*60*60:  # More than 4 hours without playtime
            if 'Bored' not in self.status:
                self.status.append('Bored')
        else:
            if 'Bored' in self.status:
                self.status.remove('Bored')

        if (current_time - last_chat_time_datetime).total_seconds() > 4*60*60:  # More than 4 hours without chatting
            if 'Sad' not in self.status:
                self.status.append('Sad')
        else:
            if 'Sad' in self.status:
                self.status.remove('Sad')

    def feed(self):
        self.hunger = max(0, self.hunger - 10)
        self.emotion = 'happy'
        self.last_fed_time = datetime.now()
        self.update_pet_status()
        self.save_info()

    def give_injection(self):
        self.health = min(100, self.health + 10)
        self.emotion = 'happy'
        self.update_pet_status()
        self.save_info()

    def play(self):
        self.emotion = 'happy'
        self.last_play_time = datetime.now()
        self.update_pet_status()
        self.save_info()
    
    def generate_reaction(self, action):
        status_description = ", ".join(self.status) if self.status else "content"
        reaction_prompt = (
            f"{self.chat_history}"
            f"As a {self.animal_type} who currently feels {status_description}, "
            f"say something when your owner {action}. Respond in a {self.characteristics[0].lower()} tone."
        )

        reaction = gemini_client.generate_text(reaction_prompt)
        self.chat_history += f"Your pet reacted: {reaction}\n"
        self.save_info(self.chat_history)
        return reaction

    @classmethod
    def normalize_statuses(cls, statuses):
        normalized = []
        for status in statuses or []:
            english = LEGACY_STATUS_TRANSLATIONS.get(status, status)
            if english not in normalized:
                normalized.append(english)
        return normalized

    @classmethod
    def clean_chat_history(cls, chat_history):
        if not chat_history:
            return ""
        cleaned = chat_history
        for old, new in LEGACY_CHAT_REPLACEMENTS.items():
            cleaned = cleaned.replace(old, new)
        return cleaned

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
