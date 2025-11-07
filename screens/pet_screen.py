from __future__ import annotations

from datetime import datetime

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from models.pet import Pet
from utils import gemini_client


class PetScreen:
    """Interactive CLI screen to care for the pet."""

    def __init__(self, console: Console, pet: Pet) -> None:
        self.console = console
        self.pet = pet

    def run(self) -> bool:
        """Main loop. Returns ``True`` if the pet reached a game over state."""
        while True:
            self.pet.update_pet_status()
            self._render_status()
            if "Morto" in self.pet.status:
                return True

            action = Prompt.ask(
                "Escolha uma ação",
                choices=["alimentar", "injeção", "brincar", "conversar", "sair"],
                default="alimentar",
            )
            if action == "alimentar":
                self._handle_feed()
            elif action == "injeção":
                self._handle_injection()
            elif action == "brincar":
                self._handle_play()
            elif action == "conversar":
                self._handle_chat()
            elif action == "sair":
                self.console.print("[cyan]Até logo![/]")
                return False

    def _render_status(self) -> None:
        table = Table(title=f"Status de {self.pet.name}")
        table.add_column("Indicador", style="bold")
        table.add_column("Valor")
        table.add_row("Saúde", str(self.pet.health))
        table.add_row("Fome", str(self.pet.hunger))
        table.add_row("Emoção", self.pet.emotion)
        table.add_row("Status", ", ".join(self.pet.status) if self.pet.status else "Normal")
        self.console.print(table)

    def _handle_feed(self) -> None:
        self.pet.feed()
        reaction = self.pet.generate_reaction("te alimenta")
        self.console.print(f"[green]Pet:[/] {reaction}")

    def _handle_injection(self) -> None:
        self.pet.give_injection()
        reaction = self.pet.generate_reaction("te da uma injecao")
        self.console.print(f"[green]Pet:[/] {reaction}")

    def _handle_play(self) -> None:
        self.pet.play()
        reaction = self.pet.generate_reaction("brinca com voce")
        self.console.print(f"[green]Pet:[/] {reaction}")

    def _handle_chat(self) -> None:
        user_input = Prompt.ask("O que você diz ao seu pet?", default="")
        if not user_input.strip():
            self.console.print("[yellow]Nenhuma mensagem enviada.[/]")
            return
        history_was_empty = not (self.pet.chat_history or "").strip()
        self._append_chat_history(f"Você: {user_input}\n")
        if history_was_empty:
            combined_prompt = f"{self.pet.generate_prompt()}\n{self.pet.chat_history}".strip()
        else:
            combined_prompt = self.pet.chat_history
        response = gemini_client.generate_text(combined_prompt)
        self._append_chat_history(f"Pet: {response}\n")
        self.console.print(f"[green]Pet:[/] {response}")
        self.pet.last_chat_time = datetime.now()
        self.pet.save_info(self.pet.chat_history)

    def _append_chat_history(self, text: str) -> None:
        if self.pet.chat_history is None:
            self.pet.chat_history = ""
        self.pet.chat_history += text
