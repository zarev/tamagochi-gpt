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
            pet = Pet(name="sem_nome", health=100, hunger=10, emotion="feliz")
            self._render_pet_preview(pet)
            action = Prompt.ask(
                "Você quer adotar este pet?",
                choices=["adotar", "tentar", "sair"],
                default="adotar",
            )
            if action == "adotar":
                name = Prompt.ask("Escolha um nome para o pet", default=pet.name)
                pet.name = name.strip() or pet.name
                pet.save_info()
                self.console.print(f"[green]Pet {pet.name} adotado![/]")
                return pet
            if action == "tentar":
                self.console.print("[cyan]Encontrando outro pet...[/]")
                continue
            self.console.print("[yellow]Adoção cancelada.[/]")
            return None

    def _render_pet_preview(self, pet: Pet) -> None:
        table = Table(title="Novo pet disponível")
        table.add_column("Atributo", style="bold")
        table.add_column("Valor")
        table.add_row("Tipo", pet.animal_type)
        table.add_row("Características", ", ".join(pet.characteristics))
        table.add_row("Saúde", str(pet.health))
        table.add_row("Fome", str(pet.hunger))
        table.add_row("Emoção", pet.emotion)
        self.console.print(table)