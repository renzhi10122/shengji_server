from flask import Flask, render_template, session
from flask_bootstrap import Bootstrap
from flask_socketio import SocketIO, emit
import shengji_server.src.deck as d

app = Flask(__name__)
Bootstrap(app)
socketio = SocketIO(app)
deck = d.Deck(2)
init_stacks = {
    "deck": [False, "0", deck.cards.copy(), False],
    "bottom": [],
    "points": [True, "25", [], False],
    "hand0": [True, "25", [], True],
    "hand1": [True, "25", [], True],
    "hand2": [True, "25", [], True],
    "hand3": [True, "25", [], True],
    "field0": [True, "0", [], False],
    "field1": [True, "0", [], False],
    "field2": [True, "0", [], False],
    "field3": [True, "0", [], False],
    "current0": [True, "25", [], True],
    "current1": [True, "25", [], True],
    "current2": [True, "25", [], True],
    "current3": [True, "25", [], True]
}
game = d.Game(init_stacks)


@app.route("/")
def main():
    return render_template("main.html",
                           trump_suit=game.trump_suit,
                           trump_rank=game.trump_rank,
                           num_cards_left=len(game.stacks["deck"].cards),
                           player=session.get("player", -1) + 1)


@socketio.on("set_player")
def set_player(player):
    session["player"] = str(player)
    update_hand()
    emit("player_selected", player)


@socketio.on("shuffle")
def on_shuffle():
    game.reset()
    deck.shuffle()
    deck.recall()
    emit("update_deck", 108, broadcast=True)
    emit("update_hand", {"hand": "", "selected": ""}, broadcast=True)
    emit("update_field", {"changed_player": 0, "played": "", "past": ""}, broadcast=True)
    emit("update_field", {"changed_player": 1, "played": "", "past": ""}, broadcast=True)
    emit("update_field", {"changed_player": 2, "played": "", "past": ""}, broadcast=True)
    emit("update_field", {"changed_player": 3, "played": "", "past": ""}, broadcast=True)
    emit("update_bottom", 0, broadcast=True)
    emit("update_reveal_bottom", "", broadcast=True)
    emit("update_points", {"cards": "", "points": 0}, broadcast=True)


def update_hand(i=-1):
    hand = game.stacks["hand" + session["player"]]
    emit("update_hand",
         {
             "hand": hand.image_names_to_csv(),
             "selected": hand.selected_to_csv(),
             "highlight": i
         })


def update_field(changed_player, new="true"):
    played = game.stacks["field" + changed_player]
    current = game.stacks["current" + changed_player]
    emit("update_field",
         {
             "changed_player": changed_player,
             "played": current.image_names_to_csv(),
             "past": played.cards[-1].image_name if played.cards else "",
             "new": new
         }, broadcast=True)


def check_session_player(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)

    if "player" not in session:
        emit("warning_player_selection")
    else:
        return wrapper


@socketio.on("trump_suit")
def on_trump_suit(i):
    if "player" not in session:
        emit("warning_player_selection")
    else:
        game.set_trump_suit(i)
        deck.assign_ranks(game.trump_suit, game.trump_rank)
        game.stacks["hand" + session["player"]].sort_cards()
        update_hand()


@socketio.on("trump_rank")
def on_trump_rank(i):
    if "player" not in session:
        emit("warning_player_selection")
    else:
        game.set_trump_rank(i)
        deck.assign_ranks(game.trump_suit, game.trump_rank)
        game.stacks["hand" + session["player"]].sort_cards()
        update_hand()


@socketio.on("into_hand")
def on_into_hand():
    if "player" not in session:
        emit("warning_player_selection")
    else:
        card = game.stacks["deck"].take_card()
        game.stacks["hand" + session["player"]].append(card)
        emit("update_deck", len(game.stacks["deck"].cards), broadcast=True)
        update_hand(game.stacks["hand" + session["player"]].cards.index(card))


@socketio.on("back_into_hand")
def on_back_into_hand(i):
    if "player" not in session:
        emit("warning_player_selection")
    else:
        played = game.stacks["field" + session["player"]]
        current = game.stacks["current" + session["player"]]
        card = current.take_card(i)
        game.stacks["hand" + session["player"]].append(card)
        update_hand(game.stacks["hand" + session["player"]].cards.index(card))
        update_field(session["player"])


@socketio.on("select_card")
def on_select_card(i):
    if "player" not in session:
        emit("warning_player_selection")
    else:
        card = game.stacks["hand" + session["player"]].cards[i]
        if card.selected == "0":
            card.selected = "20"
        else:
            card.selected = "0"
        update_hand()


@socketio.on("play_cards")
def on_play_cards():
    if "player" not in session:
        emit("warning_player_selection")
    else:
        played = game.stacks["field" + session["player"]]
        for card in game.stacks["current" + session["player"]].cards:
            played.append(card)

        hand = game.stacks["hand" + session["player"]]
        current = game.stacks["current" + session["player"]]
        current.update_cards([])
        selected_cards = [c for c in hand.cards if c.selected == "20"]
        hand.update_cards([c for c in hand.cards if c.selected == "0"])
        for card in selected_cards:
            card.selected = "0"
            current.append(card)

        update_hand()
        update_field(session["player"])


@socketio.on("from_field")
def on_from_field(player):
    if "player" not in session:
        emit("warning_player_selection")
    else:
        played = game.stacks["field" + str(player)]
        if played.cards:
            card = played.take_card()
            game.stacks["hand" + session["player"]].append(card)
            update_hand(game.stacks["hand" + session["player"]].cards.index(card))
            update_field(str(player))


@socketio.on("from_points")
def on_from_points(i):
    print("take")
    if "player" not in session:
        emit("warning_player_selection")
    else:
        points = game.stacks["points"]
        if points.cards:
            card = points.take_card(i)
            game.stacks["hand" + session["player"]].append(card)
            update_hand(game.stacks["hand" + session["player"]].cards.index(card))
            points = 0
            for card in game.stacks["points"].cards:
                if card.get_rank() == 5:
                    points += 5
                else:
                    points += 10

            emit("update_points", {"cards": game.stacks["points"].image_names_to_csv(), "points": points},
                 broadcast=True)


@socketio.on("put_bottom")
def on_put_bottom():
    if "player" not in session:
        emit("warning_player_selection")
    else:
        hand = game.stacks["hand" + session["player"]]
        bottom = game.stacks["bottom"]
        selected_cards = [c for c in hand.cards if c.selected == "20"]
        hand.update_cards([c for c in hand.cards if c.selected == "0"])
        for card in selected_cards:
            card.selected = "0"
            bottom.append(card)

        if len(bottom.cards) == 8:
            init_str = ""
            init_str += "".join(
                [str(card.get_rank()) + "_" + str(card.get_suit()) + "," for card in game.stacks["hand0"].cards])
            init_str += "".join(
                [str(card.get_rank()) + "_" + str(card.get_suit()) + "," for card in game.stacks["hand1"].cards])
            init_str += "".join(
                [str(card.get_rank()) + "_" + str(card.get_suit()) + "," for card in game.stacks["hand2"].cards])
            init_str += "".join(
                [str(card.get_rank()) + "_" + str(card.get_suit()) + "," for card in game.stacks["hand3"].cards])
            init_str += "".join(
                [str(card.get_rank()) + "_" + str(card.get_suit()) + "," for card in game.stacks["bottom"].cards])
            init_str += str(game.trump_suit) + ","
            init_str += str(game.trump_rank) + ","
            game.to_be_saved = init_str

        update_hand()
        emit("update_bottom", len(bottom.cards), broadcast=True)


@socketio.on("from_bottom")
def on_from_bottom():
    if "player" not in session:
        emit("warning_player_selection")
    else:
        bottom = game.stacks["bottom"]
        card = bottom.take_card()
        game.stacks["hand" + session["player"]].append(card)
        update_hand(game.stacks["hand" + session["player"]].cards.index(card))
        emit("update_bottom", len(bottom.cards), broadcast=True)


@socketio.on("reveal_bottom")
def on_reveal_bottom():
    if "player" not in session:
        emit("warning_player_selection")
    else:
        emit("update_reveal_bottom", game.stacks["bottom"].image_names_to_csv(), broadcast=True)


@socketio.on("get_points")
def on_get_points():
    if "player" not in session:
        emit("warning_player_selection")
    else:
        for i in range(0, 4):
            current = game.stacks["current" + str(i)]
            for card in current.cards:
                if card.get_rank() in [5, 10, 13]:
                    game.stacks["points"].append(card)

            current.update_cards([c for c in current.cards if not c.get_rank() in [5, 10, 13]])
            update_field(str(i), "")

        points = 0
        for card in game.stacks["points"].cards:
            if card.get_rank() == 5:
                points += 5
            else:
                points += 10

        emit("update_points", {"cards": game.stacks["points"].image_names_to_csv(), "points": points}, broadcast=True)


@socketio.on("save_final_state")
def on_save_final(custom_save_value):
    if "player" not in session:
        emit("warning_player_selection")
    else:
        to_be_saved = game.to_be_saved
        to_be_saved += custom_save_value
        with open("data.txt", "a+") as f:
            f.write(to_be_saved + "\n")
        game.to_be_saved = ""


@socketio.on("no_trump_save")
def no_trump_save():
    if "player" not in session:
        emit("warning_player_selection")
    else:
        to_be_saved = game.to_be_saved
        to_be_saved += custom_save_value
        with open("data.txt", "a+") as f:
            f.write(to_be_saved + "\n")
        game.to_be_saved = ""


@socketio.on("reset_save")
def on_reset_save():
    if "player" not in session:
        emit("warning_player_selection")
    else:
        game.to_be_saved = ""


if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=80)
