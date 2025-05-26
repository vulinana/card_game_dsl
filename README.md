#Master’s Thesis

### Author: Ana Vulin, E2 62/2023
### Supervisor: Prof. Igor Dejanović, PhD
### Year: 2025

## Project theme

This master’s thesis presents the design and implementation of a Domain-Specific Language (DSL) in the domain of card games. 
The project focuses on modeling and executing turn-based card game logic using a custom textual DSL.

The game system enables the definition of rules, game progression and cards through a clear and readable DSL syntax. 
The language supports features such as turn management, conditional effects, player interactions, and winning conditions.

The project uses the textX meta-language framework to define and parse the DSL grammar.
The entire application backend, including game logic and state management, is developed with Flask in Python.
The frontend, implemented in JavaScript, communicates with the backend through WebSocket for real-time gameplay interaction.

During execution, the program loads a DSL file, validates its structure, and interprets the game logic in real time.
Players can select a game (represented by a DSL script), after which the game runs according to the defined rules.

## Run guide
To run the game you need to download the github repository and set builtin interpreter from the program,
to do this easiest way is to use pycharm, go to **File** then **Settings** after that go to **Add Interpreter** 
and add interpreter from folder **card_game_dsl** needed requirements of packages can be found in **requirements.txt** file.

## DSL Specification
The custom Domain-Specific Language (DSL) for card games is designed to provide a simple, readable, and expressive way to define the structure and rules of turn-based card games. 
The specification is organized into clearly separated blocks: game, rules, states, and cards. Each of these blocks plays a specific role in describing the gameplay.

### game block
Defines the name of the game. This is the root declaration under which all other definitions (rules, states, and cards) are grouped.

```
game Tablic
```

### rules block
Specifies the foundational rules and constraints for the game. These parameters determine how the game operates and ends.

```
rules
  min_players 2
  max_players 3
  rounds 2
  table_cards_visible true
  next_player_in_round_condition last_played
  game_winner highest_score
```

### states block
Defines the game flow using a state machine model. Each state represents a step in gameplay that includes an action (do) and one or more possible transitions (then) to other states.

There are three types of transitions depending on how many then statements are defined and whether they use conditions.

#### Single transition – always follows the same path
```
state deal_table_cards
  do deal_table_cards(2)
  then deal_player_cards
```

####  Multiple conditional transitions – based on game logic
If there are multiple then statements and each has an if condition, the next state is selected based on the evaluation of conditions.
```
state next_player
  do next_player
  then throw_cards
  then action2
```

####  Multiple transitions without conditions – player's choice
If a state contains multiple then statements without conditions, the transition depends on a player's decision or some runtime input, representing branching gameplay.
```
state validate_cards_selection
  do cards_selection_sum_matching
  then mark_matching_cards_for_scoring if true
  then notify_player_of_invalid_move if false
```

### cards block
Defines the complete deck of cards used in the game. Each card entry includes its value, suit, number of appearances, and point value.

```
    card 5 of hearts appears 4 times, worth 0 points
    card 13 of hearts appears 4 times, worth 0 points
    card 5 of diamonds appears 4 times, worth 0 points
    card 10 of clubs appears 4 times, worth 10 points
```

  
