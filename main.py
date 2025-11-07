import json
import os
from typing import Optional

from rich.console import Console
from rich.panel import Panel

from models.pet import Pet
from screens.adoption_screen import AdoptionScreen
from screens.game_over_screen import GameOverScreen
from screens.pet_screen import PetScreen


class PetGameApp:
    """Simple terminal application wrapper for the Tamagochi pet."""

    def __init__(self, console: Console) -> None:
        self.console = console

    def run(self) -> None:
        self.console.print(Panel.fit("[bold magenta]Bem-vindo ao Tamagochi GPT![/]"))
        pet = self._load_pet_from_save_file()
        if pet is None:
            adoption_screen = AdoptionScreen(self.console)
            pet = adoption_screen.choose_pet()
            if pet is None:
                self.console.print("[yellow]Até a próxima![/]")
                return
        pet_screen = PetScreen(self.console, pet)
        game_over = pet_screen.run()
        if game_over:
            GameOverScreen(self.console, pet).show()
        self.console.print("[green]Jogo encerrado.[/]")

    def _load_pet_from_save_file(self) -> Optional[Pet]:
        save_file_path = "save_file.txt"
        if not os.path.exists(save_file_path):
            return None

        with open(save_file_path, "r", encoding="utf-8") as file:
            pet_data = json.load(file)

        pet = Pet(
            pet_data.get("name", "Pet"),
            pet_data.get("health", 100),
            pet_data.get("hunger", 0),
            pet_data.get("emotion", "feliz"),
            chat_history=pet_data.get("chat_history", ""),
            image_number=pet_data.get("image_number"),
            last_fed_time=pet_data.get("last_fed_time"),
            last_play_time=pet_data.get("last_play_time"),
            last_chat_time=pet_data.get("last_chat_time"),
        )
        pet.animal_type = pet_data.get("animal_type", pet.animal_type)
        pet.characteristics = pet_data.get("characteristics", pet.characteristics)
        pet.status = pet_data.get("status", pet.status)
        return pet


if __name__ == "__main__":
    console = Console()
    app = PetGameApp(console)
    app.run()
