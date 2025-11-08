from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from models.pet import Pet


class AdoptionScreen:
    """CLI adoption flow that replaces the previous Kivy screen."""

    def __init__(self, console: Console) -> None:
        self.console = console

    def choose_pet(self) -> Optional[Pet]:
        """Return an adopted pet or ``None`` if the user cancels."""
        while True:
            pet = Pet(name="no_name", health=100, hunger=10, emotion="happy")
            self._render_pet_preview(pet)
            action = Prompt.ask(
                "Do you want to adopt this pet?",
                choices=["adopt", "reroll", "leave"],
                default="adopt",
            )
            if action == "adopt":
                name = Prompt.ask("Choose a name for the pet", default=pet.name)
                pet.name = name.strip() or pet.name
                pet.save_info()
                self.console.print(f"[green]Pet {pet.name} adopted![/]")
                return pet
            if action == "reroll":
                self.console.print("[cyan]Finding another pet...[/]")
                continue
            self.console.print("[yellow]Adoption cancelled.[/]")
            return None

    def _render_pet_preview(self, pet: Pet) -> None:
        table = Table(title="New pet available")
        table.add_column("Attribute", style="bold")
        table.add_column("Value")
        table.add_row("Type", pet.animal_type)
        table.add_row("Traits", ", ".join(pet.characteristics))
        table.add_row("Health", str(pet.health))
        table.add_row("Hunger", str(pet.hunger))
        table.add_row("Emotion", pet.emotion)
        self.console.print(table)