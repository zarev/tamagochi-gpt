from __future__ import annotations

from io import BytesIO

from rich.console import Console
from rich.panel import Panel

from PIL import Image as PILImage

from utils import gemini_client


class GameOverScreen:
    """Terminal feedback when the pet reaches a game over state."""

    def __init__(self, console: Console, pet) -> None:
        self.console = console
        self.pet = pet

    def show(self) -> None:
        image_path = self._generate_dead_image()
        message = (
            f"Your pet {self.pet.name} unfortunately passed away.\n"
            f"A farewell image was saved to: {image_path}"
        )
        self.console.print(Panel.fit(message, title="Game Over", style="red"))

    def _generate_dead_image(self) -> str:
        prompt = (
            f"a 16 bit pixel art of a dead {self.pet.animal_type} like a tamagotchi on a black background"
        )
        image_bytes = gemini_client.generate_image(prompt)
        image = PILImage.open(BytesIO(image_bytes))
        img_path = "assets/pet_animations/pet_dead.png"
        image.save(img_path)
        return img_path
