import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gme.utils import load_game_model
from graphviz import Digraph


def generate_diagram(game_name):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    game_file_path = os.path.join(base_dir, 'gme', 'games', f"{game_name}.gme")

    if not os.path.isfile(game_file_path):
        print(f"Game file not found: {game_file_path}")
        sys.exit(1)

    game = load_game_model(game_file_path)

    dot = Digraph(comment='Card Game State Machine')
    dot.attr(rankdir='TB')
    dot.attr('node', style='filled', fontname='Helvetica', shape='box', fillcolor='lightblue')

    for state in game.states:
        params = ', '.join(str(p) for p in state.action.params)
        action_label = f"{state.action.name}({params})" if params else state.action.name
        label = f"{state.name}\n[do: {action_label}]"
        dot.node(state.name, label=label)

    for state in game.states:
        for transition in state.transitions:
            label = ''
            if transition.condition is not None:
                label = f"if {transition.condition}".lower()
            color = 'black'
            if str(transition.condition).lower() == 'false':
                color = 'red'
            elif str(transition.condition).lower() == 'true':
                color = 'green'
            dot.edge(state.name, transition.nextState, label=label, color=color)

    output_path = os.path.join(base_dir, 'static', 'game_photos', game_name)
    dot.format = 'png'
    dot.render(output_path, cleanup=True)
    image_path = f"{output_path}.png"
    print(f"Diagram generated at {image_path}")

    try:
        if sys.platform.startswith('win'):
            os.startfile(image_path)
        elif sys.platform.startswith('darwin'):
            os.system(f"open \"{image_path}\"")
        else:
            os.system(f"xdg-open \"{image_path}\"")
    except Exception as e:
        print(f"Failed to open image automatically: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_game_diagram.py <game_name>")
        sys.exit(1)

    game_name = sys.argv[1]
    print(game_name)
    generate_diagram(game_name)
