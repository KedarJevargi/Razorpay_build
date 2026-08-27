import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.theme import Theme

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client.buyer_agent import BuyerAgent

custom_theme = Theme({
    "buyer": "cyan",
    "merchant": "green",
    "system": "yellow"
})
console = Console(theme=custom_theme)

def log_callback(role: str, message: str):
    if role == "buyer":
        console.print(Panel(message, title="[bold cyan]Buyer Agent[/bold cyan]", border_style="cyan"))
    elif role == "merchant":
        console.print(Panel(message, title="[bold green]Merchant Orchestrator[/bold green]", border_style="green"))
    elif role == "system":
        console.print(f"[system]⚙️ {message}[/system]")
    else:
        console.print(message)

def main():
    console.clear()
    console.print(Panel.fit(
        "[bold magenta]Welcome to the A2A Buyer Agent (Test Harness)[/bold magenta]\n"
        "Enter your high-level purchasing goal, and the agent will negotiate with the merchant on your behalf.",
        title="Agent-to-Agent Commerce"
    ))
    
    goal = Prompt.ask("\n[bold]Enter your goal[/bold] (leave blank for default)")
    if not goal:
        goal = "I have a budget of 10,000 INR. Find me the best waterproof tent. Add it to my cart."
        console.print(f"[dim]Using default goal: {goal}[/dim]")
        
    console.print("\n[bold yellow]Initializing Buyer Agent...[/bold yellow]")
    agent = BuyerAgent()
    
    console.print("\n[bold yellow]Handing over to autonomous agent...[/bold yellow]\n")
    try:
        final_response = agent.process_goal(goal, log_callback)
        console.print(Panel(final_response, title="[bold magenta]Final Outcome[/bold magenta]", border_style="magenta"))
    except Exception as e:
        console.print(f"[bold red]Fatal Error:[/bold red] {e}")

if __name__ == "__main__":
    main()
