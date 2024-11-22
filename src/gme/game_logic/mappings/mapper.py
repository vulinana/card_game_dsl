from ..DTO.CardGameDTO import CardGameDTO

def map_card_game_to_json(card_game_model):
    return {
        'name': card_game_model.name,
    }