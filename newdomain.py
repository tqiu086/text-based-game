import argparse
import json
import socket
from aiohttp import web
from aiohttp.web import Request, Response, json_response
from asyncio import Lock

# global state
domain_id = None
domain_secret = None
user_state = {}
item_definitions = {}
user_url = None

state_lock = Lock()

# define terminal password texts
terminal_texts = {
    "liu": """I was born during the "Age of Braking," a time of upheaval and transformation. With the sun on the brink of destruction, humanity launched the "Wandering Earth Project," turning Earth into a spaceship propelled by colossal planetary engines. The engines’ activation brought catastrophic climate changes: raging blizzards and environmental collapse. Society fractured, with some supporting the plan as humanity's only hope, while others denounced it as madness. My family supported the project, but doubts lingered within me. Watching the world around us crumble was harrowing, but the unwavering resolve of those around me kept us going. Despite unimaginable sacrifices, humanity succeeded in slowing Earth's orbit, preparing for the next phase: escaping the solar system.""",
    "lang": """Earth finally left the solar system, plunging into the darkness of deep space. This marked the beginning of the "Age of Escape," a time of freezing cold and endless night. Life on the surface became impossible, forcing us to move to underground cities. Resources were scarce, and every scrap of food or warmth was precious. I saw people lose hope and succumb to madness, but others displayed incredible resilience and kindness. My family persevered, clinging to each other for survival. Without sunlight, we often reminisced about the blue skies of the past. Yet, our desire to see the future kept us alive. In this endless darkness, we held on to a fragile belief: someday, light would return.""",
    "di": """As the journey stretched on, doubts about the project began to fester, culminating in a large-scale rebellion. Some believed the "Wandering Earth Project" was doomed to fail, advocating for abandoning Earth to search for habitable planets. The rebellion threatened to sabotage the engines and humanity’s survival. I witnessed the chaos and cruelty of conflict, the moral dilemmas tearing apart families and communities. Amidst this turmoil, I saw both the best and worst of humanity. Though we faced unimaginable loss, the rebellion was eventually quashed. This painful chapter left scars but also strengthened our resolve. United once more, humanity refocused on its shared mission of survival, albeit with lingering wounds from the conflict.""",
    "qiu": """Now, we live in the "Age of Wandering," a long and stable period of our journey. Life in the underground cities has become the new normal, and we’ve adapted to the darkness. My generation knows little of sunlight, while older generations still long for the past. Society has evolved, reshaping relationships between people and nature. Despite the isolation and the passage of time, hope flickers on the horizon. Recently, scientists reported that Earth is nearing a new star system. This news ignites a sense of purpose within us. For the first time, I can envision a new beginning. Our journey through the void has taught us to revere the cosmos and believe that humanity’s endurance will lead to a brighter future. (I can explore more)""",
    "liu lang di qiu": """Whenever I hear this song, a warm current flows into my old and stiff body, and my dry old eyes become moist again. I seem to see three golden suns of Centaurus rising at the same time on the horizon, and everything is bathed in its warm light. The solid air melts and becomes a blue sky. The seeds from more than 2,000 years ago revive from the thawed soil, and the earth turns green... I see her, she runs towards me from the green earth, young and beautiful, like an angel...

Ah, Earth, my wandering Earth...

— Story from the wandering earth by Cixin Liu (2012). If you are interested, please take a look over domain 101, thank you""",
    "her": """Our story began during the "Age of Braking," a time of despair and hope intertwined. I first met her at a supply distribution point, where she was mistaken for a thief after helping a neighbor. I stepped forward to defend her. From that moment on, we supported each other, finding light amid the cold. Back then, childbirth required a lottery. When we won the right, she leapt with joy, spinning like a child and holding my hand as she dreamed about our future child. In that moment, I vowed to protect her and her smile.
However, as Earth drifted into deep space, she began to question the truth behind the "Wandering Earth Project" and ultimately joined the rebels. I later learned that she died heroically on the battlefield, clutching a rifle and giving her life for her beliefs. Her death left me lost. I supported the plan, but I couldn’t deny her choice. Years later, as an old man, I dreamed of her in her wedding dress, gracefully dancing. I wanted to apologize to her, but I could only watch her fade away, leaving me with endless regret and longing. (qiu)""",
    "photo": """Our story began during the "Age of Braking," a time of despair and hope intertwined. I first met her at a supply distribution point, where she was mistaken for a thief after helping a neighbor. I stepped forward to defend her. From that moment on, we supported each other, finding light amid the cold. Back then, childbirth required a lottery. When we won the right, she leapt with joy, spinning like a child and holding my hand as she dreamed about our future child. In that moment, I vowed to protect her and her smile.
However, as Earth drifted into deep space, she began to question the truth behind the "Wandering Earth Project" and ultimately joined the rebels. I later learned that she died heroically on the battlefield, clutching a rifle and giving her life for her beliefs. Her death left me lost. I supported the plan, but I couldn’t deny her choice. Years later, as an old man, I dreamed of her in her wedding dress, gracefully dancing. I wanted to apologize to her, but I could only watch her fade away, leaving me with endless regret and longing. (qiu)""",
    "medal": """Father got this medal as one of the engineers of the wandering earth project, which was a true gift proving his wisdom and sacrifice. I questioned about his purpose so hard when the project was believed as a lie. But dad is dad, every time when they talk about the project, I remember him and miss him, and I hold his medal in my hand. (lang)""",
    "story": """Whenever I hear this song, a warm current flows into my old and stiff body, and my dry old eyes become moist again. I seem to see three golden suns of Centaurus rising at the same time on the horizon, and everything is bathed in its warm light. The solid air melts and becomes a blue sky. The seeds from more than 2,000 years ago revive from the thawed soil, and the earth turns green... I see her, she runs towards me from the green earth, young and beautiful, like an angel...

Ah, Earth, my wandering Earth...

— Story from the wandering earth by Cixin Liu (2012). If you are interested, please take a look over domain 101, thank you"""
}

# define items
game_items = {
    "poem": {
        "id": None,
        "name": "poem",
        "description": None,
        "verbs": {
            "look": "a short paper with words, trying to tell you to type hint if everything’s too hard",
            "read": """I know I have been long forgotten,
For the journey drifts on, endless and vast.
But call out to me in that fleeting moment,
When dawn's light returns to the eastern skies.
I know I have been long forgotten,
For the days of departure are distant and dim.
But call out to me in that fleeting moment,
When humanity beholds the blue sky again.
I know I have been long forgotten,
For the tales of the solar system fade in time.
But call out to me in that fleeting moment,
When blossoms once more adorn the boughs.
(liu)"""
        },
        "location": "up",
        "depth": 0
    },
    "medal": {
        "id": None,
        "name": "medal",
        "description": None,
        "verbs": {
            "look": "A medal with blood, someone’s been holding it very tightly."
        },
        "location": "left",
        "depth": 1
    },
    "her photo": {
        "id": None,
        "name": "her photo",
        "description": None,
        "verbs": {},
        "location": "right",
        "depth": 0
    },
    "story book wandering earth": {
        "id": None,
        "name": "story book wandering earth",
        "description": None,
        "verbs": {
            "look": "Wanna read it?"
        },
        "location": "down",
        "depth": 2
    },
    "terminal": {
        "id": None,
        "name": "terminal",
        "description": "A screen with keyboard, command: use terminal <key>",
        "verbs": {},
        "location": "mid",
        "depth": 0,
        "not_takeable": True
    }
}

# define rooms
game_rooms = {
    "up": {
        "name": "up",
        "description": "A prison cell, but someone broke the bar on the south.",
        "connections": {
            "south": "mid"
        },
        "items": ["poem"]
    },
    "mid": {
        "name": "mid",
        "description": "A room looks like the operating room to a plane, path to the four ways.",
        "connections": {
            "north": "up",
            "west": "left",
            "east": "right",
            "south": "down"
        },
        "items": ["terminal"]
    },
    "left": {
        "name": "left",
        "description": "That was, the house you used to live?",
        "connections": {
            "east": "mid"
        },
        "items": ["medal"]
    },
    "right": {
        "name": "right",
        "description": "A girl’s living room. I’m confused why it looks like this.",
        "connections": {
            "west": "mid"
        },
        "items": ["her photo"]
    },
    "down": {
        "name": "down",
        "description": "The floor is fading away, I feel like I’m floating.",
        "connections": {
            "north": "mid"
        },
        "items": ["story book wandering earth"]
    }
}

routes = web.RouteTableDef()

@routes.post('/newhub')
async def handle_newhub(req: Request) -> Response:
    global domain_id, domain_secret, user_state, game_items, user_url

    url = await req.text()
    user_url = url
    serialized_items = list(game_items.values())

    async with req.app['client'].post(f"{url}/register", json={
        'url': whoami,
        'name': "MP-NEWGAME",
        'description': "Welcome to my game!",
        'items': serialized_items,
    }) as resp:
        txt = await resp.text()
        try:
            data = json.loads(txt)
        except json.JSONDecodeError:
            return json_response({"error": "Hub returned non-JSON response", "body": txt}, status=500)

        if 'error' in data:
            return json_response(status=resp.status, data=data)

        if not all(k in data for k in ('id', 'secret', 'items')):
            return json_response({"error": "Missing fields from hub response", "data": data}, status=500)

        domain_id = data['id']
        domain_secret = data['secret']
        user_state.clear()

        assigned_items = data.get('items', [])
        for i, assigned_id in enumerate(assigned_items):
            if i < len(serialized_items):
                item_name = serialized_items[i]['name']
                for iname, itm in game_items.items():
                    if itm["name"] == item_name:
                        itm["id"] = assigned_id
                        item_definitions[assigned_id] = itm

    return json_response({'ok': 'registered'})

@routes.post('/arrive')
async def handle_arrive(req: Request) -> Response:
    global domain_secret, user_state, item_definitions

    data = await req.json()
    if data.get('secret') != domain_secret:
        return json_response({"error": "invalid secret"}, status=403)

    user_id = data['user']
    owned = data.get('owned', [])
    carried = data.get('carried', [])
    dropped = data.get('dropped', [])
    prize = data.get('prize', [])

    async with state_lock:
        if user_id not in user_state:
            user_state[user_id] = {
                "location": "up",
                "inventory": {
                    "owned": [],
                    "carried": carried,
                },
                "dropped": dropped,
                "prize": prize,
                "visited": set(),
                "present": True,
                "photo_looked": False,
                "somewhere_unlocked": False,  # per-user
                "qiu_entered": False          # per-user
            }
        else:
            user_state[user_id]["present"] = True

        user_state[user_id]["inventory"]["carried"] = carried
        user_state[user_id]["dropped"] = dropped
        user_state[user_id]["prize"] = prize

        for item in owned + carried + dropped + prize:
            if isinstance(item, dict):
                item_id = item.get("id")
                if item_id and item_id not in item_definitions:
                    item_definitions[item_id] = item
            else:
                itm = game_items.get(item)
                if itm and itm["id"] not in item_definitions:
                    item_definitions[itm["id"]] = itm

    return web.Response(status=200)

@routes.post('/dropped')
async def handle_dropped(req: Request) -> Response:
    global domain_secret, user_state, item_definitions

    data = await req.json()
    if data.get('secret') != domain_secret:
        return json_response({"error": "invalid secret"}, status=403)

    user_id = data.get('user')
    item_id = data.get('item')

    if isinstance(item_id, dict):
        item_id = item_id.get('id')
    if not isinstance(item_id, (str, int)):
        return json_response({"error": "invalid item ID"}, status=400)

    item_name = None
    for item_data in game_items.values():
        if item_data['id'] == item_id:
            item_name = item_data['name']
            break

    if user_id in user_state and item_name and item_name in user_state[user_id]['inventory']['owned']:
        user_state[user_id]['inventory']['owned'].remove(item_name)

    async with state_lock:
        if user_id not in user_state:
            return json_response({"error": "user not found"}, status=404)

        current_location = user_state[user_id]["location"]
        if item_id in item_definitions:
            item_definitions[item_id]["location"] = current_location
        else:
            item_definitions[item_id] = {"id": item_id, "location": current_location}

        user_state[user_id].setdefault("dropped", []).append({
            "id": item_id,
            "location": current_location
        })

    return json_response({"location": current_location})

@routes.post('/depart')
async def handle_depart(req: Request) -> Response:
    global domain_secret, user_state

    data = await req.json()
    if data.get('secret') != domain_secret:
        return json_response({"error": "invalid secret"}, status=403)

    user_id = data.get('user')

    async with state_lock:
        if user_id not in user_state:
            return json_response({"error": "user not found"}, status=404)
        user_state[user_id]["present"] = False

    print(f"User {user_id} has departed the domain.")
    return json_response({"ok": f"User {user_id} has departed."})

def user_owns_item(user_id, name):
    inv_list = user_state[user_id]["inventory"]["owned"] + [
        x["name"] if isinstance(x, dict) else x for x in user_state[user_id]["inventory"]["carried"]
    ]
    return any(x.lower() == name.lower() for x in inv_list)

def describe_location(user_id, room_name):
    r = game_rooms.get(room_name, {})
    description = r.get("description", "You are somewhere.")
    return description

def get_items_in_location(user_id, location):
    room_items = []
    user_info = user_state[user_id]
    r = game_rooms.get(location, {})
    if not r:
        return room_items

    user_owned = [x.lower() for x in (user_info["inventory"]["owned"] + [x["name"] if isinstance(x, dict) else x for x in user_info["inventory"]["carried"]])]

    # room's original items
    for i_name in r.get("items", []):
        itm = game_items.get(i_name)
        if itm and itm["name"].lower() not in user_owned:
            room_items.append((itm["name"], itm["id"]))

    for d in user_info.get("dropped", []):
        if d["location"] == location:
            itdef = item_definitions.get(d["id"], {})
            iname = itdef.get("name", f"item {d['id']}")
            if iname.lower() not in user_owned:
                iid = itdef.get("id", d["id"])
                room_items.append((iname, iid))

    prize = user_info.get("prize", [])
    prize_items_by_depth = {}
    for p in prize:
        if isinstance(p, dict):
            p_name = p.get("name", "item")
            p_depth = p.get("depth", 0)
            p_id = p.get("id")
        else:
            p_name = p
            p_depth = 0
            p_id = None
            for itv in game_items.values():
                if itv["name"].lower() == p_name.lower():
                    p_depth = itv.get("depth", 0)
                    p_id = itv.get("id")
                    break
        prize_items_by_depth.setdefault(p_depth, []).append((p_name, p_id))

    depth_display = None
    if location == "left":
        depth_display = 0
    elif location == "right":
        depth_display = 1
    elif location == "down":
        depth_display = 2

    if depth_display is not None:
        items = prize_items_by_depth.get(depth_display, [])
        for name, pid in items:
            if name.lower() not in user_owned:
                room_items.append((name, pid if pid else "unknown"))

    return room_items

def find_item_by_id(item_id):
    if item_id in item_definitions:
        return item_definitions[item_id]
    for itv in game_items.values():
        if itv.get("id") == item_id:
            return itv
    return None

def get_item_by_name_or_id(user_id, target, location):
    user_info = user_state[user_id]

    visible_items = get_items_in_location(user_id, location)
    for (iname, iid) in visible_items:
        if iname.lower() == target.lower() or str(iid) == target:
            # If it's a prize item with real ID
            if isinstance(iid, str) and not iid.startswith("prize:"):
                # This is a prize item with real ID
                return {"name": iname, "id": iid, "is_prize_item": True}
            for itv in game_items.values():
                if itv["name"].lower() == iname.lower():
                    return itv
            for itv in item_definitions.values():
                if itv.get("name", "").lower() == iname.lower():
                    return itv

    inv_list = user_info["inventory"]["owned"] + [
        x["name"] if isinstance(x, dict) else x for x in user_info["inventory"]["carried"]
    ]
    for inv_item_name in inv_list:
        if inv_item_name.lower() == target.lower():
            for itv in game_items.values():
                if itv["name"].lower() == target.lower():
                    return itv
            for itv in item_definitions.values():
                if itv.get("name", "").lower() == target.lower():
                    return itv

    for key, val in item_definitions.items():
        if str(key) == target:
            return val

    for itv in game_items.values():
        if itv.get("id") and str(itv["id"]) == target:
            return itv

    return None

def user_has_medal_or_depth1(user_id):
    user_info = user_state[user_id]
    # loop prize
    for item in user_info.get("prize", []):
        if isinstance(item, dict):
            pname = item.get("name", "item")
            p_depth = item.get("depth", 0)
        else:
            pname = item
            p_depth = 0
            for itv in game_items.values():
                if itv["name"].lower() == pname.lower():
                    p_depth = itv.get("depth", 0)
                    break
        if p_depth == 1:
            return True

    # owned items
    for owned_name in user_info["inventory"]["owned"]:
        for itv in game_items.values():
            if itv["name"].lower() == owned_name.lower() and itv.get("depth", 0) == 1:
                return True
    return False

def user_has_key_in_prize(user_id):
    user_info = user_state[user_id]
    for item in user_info.get("prize", []):
        pname = item["name"] if isinstance(item, dict) else item
        if pname.lower() == "key":
            return True
    return False

@routes.post("/command")
async def handle_command(req: Request) -> Response:
    global user_state, game_items, game_rooms, domain_id, domain_secret, user_url

    data = await req.json()
    user_id = data.get('user')
    command = data.get('command', [])

    if not command:
        return web.Response(text="You must enter a command.", status=400)

    async with state_lock:
        if user_id not in user_state:
            return web.Response(text="You have to journey to this domain first.", status=403)
        if not user_state[user_id].get("present", False):
            return web.Response(text="Come back to say hello.", status=409)

        user_info = user_state[user_id]
        location = user_info["location"]
        verb = command[0].lower()
        args = command[1:]

        # handle 'go' or 'move' commands
        if verb in ["go", "move"]:
            if args:
                verb = args[0].lower()

        directions = ["north", "south", "east", "west"]
        if verb in directions:
            current_room = game_rooms.get(location, {})
            connections = current_room.get("connections", {})
            if verb in connections:
                target = connections[verb]
                # movement restrictions
                if location == "mid" and target == "left":
                    if not user_info.get("somewhere_unlocked", False):
                        return web.Response(text="You need a key in your mind", status=200)
                if location == "mid" and target == "right":
                    if not user_has_medal_or_depth1(user_id):
                        return web.Response(text="precious treasure in your hand will give courage in your heart to enter", status=200)
                if location == "mid" and target == "down":
                    if not user_info.get("qiu_entered", False) and not user_has_key_in_prize(user_id):
                        return web.Response(text="I will have to have, a real key, or the last chapter of my story", status=200)

                user_info["location"] = target
                desc = describe_location(user_id, target)
                items_in_new_location = get_items_in_location(user_id, target)
                if items_in_new_location:
                    desc += "\n" + "\n".join([f"There is a {name} <sub>(ID: {item_id})</sub> here." for name, item_id in items_in_new_location])
                return web.Response(text=desc, status=200)
            else:
                return web.Response(text="You can't go that way from here.", status=200)


        if verb == "look":
            if not args:
                base_description = describe_location(user_id, location)
                items_in_location = get_items_in_location(user_id, location)
                if items_in_location:
                    base_description += "\n" + "\n".join(
                        [f"There is a {name} <sub>(ID: {item_id})</sub> here." for name, item_id in items_in_location]
                    )
                return web.Response(text=base_description)
            else:
                target = " ".join(args)
                if target.lower() == "hint":
                    return web.Response(text="Type “liu lang di qiu” to the terminal to win the game. But I also wish you could type in each single word as well as the name of the items to know more. Have fun.")

                itm = get_item_by_name_or_id(user_id, target, location)
                if not itm:
                    return web.Response(text="I don't know how to do that.")

                takeable_items = ["poem", "medal", "her photo", "story book wandering earth"]
                if itm["name"].lower() in takeable_items:
                    if not user_owns_item(user_id, itm["name"]):
                        return web.Response(text="You don't have that item to look at.")

                    # Special case: story book wandering earth look
                    if itm["name"].lower() == "story book wandering earth":
                        return web.Response(text="Wanna read it?")
                    if itm["name"].lower() == "her photo":
                        if not user_info["photo_looked"]:
                            user_info["photo_looked"] = True
                            return web.Response(text="I don’t want to recall")
                        else:
                            return web.Response(text="on the back there’s a word: 'di'?")
                    else:
                        return web.Response(text=itm["verbs"].get("look", "I don't know how to do that."))

                if itm["name"].lower() == "terminal":
                    return web.Response(text=itm["description"])

                return web.Response(text=itm.get("description", "I don't know how to do that."))

        # handle 'read' command
        elif verb == "read":
            if not args:
                return web.Response(text="Read what?")
            target = " ".join(args)
            itm = get_item_by_name_or_id(user_id, target, location)
            if not itm:
                return web.Response(text="I don't know how to do that.")
            takeable_items = ["poem", "medal", "her photo", "story book wandering earth"]
            if itm["name"].lower() in takeable_items:
                if not user_owns_item(user_id, itm["name"]):
                    return web.Response(text="You don't have that item to read.")

                # special case story book wandering earth read -> replaced text
                if itm["name"].lower() == "story book wandering earth":
                    return web.Response(text=terminal_texts["story"])
                else:
                    return web.Response(text=itm["verbs"].get("read", "I don't know how to do that."))
            else:
                return web.Response(text="I don't know how to do that.")

        elif verb == "take":
            if not args:
                return web.Response(text="Take what?")
            target = " ".join(args)

            itm = get_item_by_name_or_id(user_id, target, location)
            if not itm:
                return web.Response(text=f"There's no {target} here to take")
            if itm.get("not_takeable"):
                return web.Response(text="You can't take that.")

            # if it's a prize item with real ID
            if itm.get("is_prize_item"):
                # the item is from the user's prize
                prize_list = user_info.get("prize", [])
                found = False
                for p in prize_list[:]:
                    p_name = p["name"] if isinstance(p, dict) else p
                    p_id = p.get("id") if isinstance(p, dict) else None
                    if p_name.lower() == itm["name"].lower() and (not p_id or p_id == itm["id"]):
                        prize_list.remove(p)
                        found = True
                        break
                if found:
                    user_info["inventory"]["owned"].append(itm["name"])
                    return web.Response(text=f"You take the {target}.")
                else:
                    return web.Response(text="You can't take that.")

            # normal item logic
            if itm["name"].lower() in [x.lower() for x in user_info["inventory"]["owned"]]:
                return web.Response(text=f"You already have the {target}.")

            # ff dropped item, remove from dropped
            user_dropped = user_info.get("dropped", [])
            for d in user_dropped[:]:
                itdef = item_definitions.get(d["id"])
                iname = itdef.get("name", "").lower() if itdef else ""
                iid = itdef.get("id", d["id"]) if itdef else d["id"]
                if (iname == target.lower() or str(iid) == target) and d["location"] == location:
                    user_dropped.remove(d)

            user_info["inventory"]["owned"].append(itm["name"])

            if itm.get("id"):
                async with req.app['client'].post(f"{user_url}/transfer", json={
                    'domain': domain_id,
                    'secret': domain_secret,
                    'user': user_id,
                    'item': itm['id'],
                    'to': "inventory"
                }) as resp:
                    await resp.text()

            return web.Response(text=f"You take the {target}.")

        # handle 'drop' command
        elif verb == "drop":
            if not args:
                return web.Response(text="Drop what?")
            target = " ".join(args)
            inv_list = user_info["inventory"]["owned"]
            item_to_drop = None
            item_to_drop_id = None
            for owned_name in inv_list:
                if owned_name.lower() == target.lower():
                    item_to_drop = owned_name
                    for itv in game_items.values():
                        if itv["name"].lower() == owned_name.lower():
                            item_to_drop_id = itv["id"]
                            break
                    break
            if not item_to_drop:
                for owned_name in inv_list:
                    for itv in game_items.values():
                        if itv["name"].lower() == owned_name.lower() and itv.get("id"):
                            if str(itv["id"]) == target:
                                item_to_drop = owned_name
                                item_to_drop_id = itv["id"]
                                break
                    if item_to_drop:
                        break

            if not item_to_drop:
                return web.Response(text=f"You don't have {target}.")

            inv_list.remove(item_to_drop)
            user_info.setdefault("dropped", []).append({
                "id": item_to_drop_id,
                "location": user_info["location"]
            })
            if item_to_drop_id and item_to_drop_id in item_definitions:
                item_definitions[item_to_drop_id]["location"] = user_info["location"]

            return web.Response(text=f"You drop the {target}.")

        # handle 'use' command
        elif verb == "use":
            if not args:
                return web.Response(text="Use what?")
            if args[0].lower() == "terminal":
                if location != "mid":
                    return web.Response(text="You can only use the terminal in the mid room.")

                if len(args) > 1:
                    password = " ".join(args[1:])
                    if password == "liu":
                        response_text = terminal_texts["liu"]
                        if not user_info.get("somewhere_unlocked", False):
                            user_info["somewhere_unlocked"] = True
                            response_text += "\n(somewhere unlocked)"
                        return web.Response(text=response_text)
                    elif password == "lang":
                        return web.Response(text=terminal_texts["lang"])
                    elif password == "di":
                        return web.Response(text=terminal_texts["di"])
                    elif password == "qiu":
                        response_text = terminal_texts["qiu"]
                        if not user_info.get("qiu_entered", False):
                            user_info["qiu_entered"] = True
                            if not user_info.get("somewhere_unlocked", False):
                                user_info["somewhere_unlocked"] = True
                                response_text += "\n(somewhere unlocked)"
                        return web.Response(text=response_text)
                    elif password == "liu lang di qiu":
                        response_text = terminal_texts["liu lang di qiu"]
                        # User wins the game
                        payload = {
                            "domain": domain_id,
                            "secret": domain_secret,
                            "user": user_id,
                            "score": 1.0
                        }
                        try:
                            async with req.app['client'].post(f"{user_url}/score", json=payload) as resp_score:
                                await resp_score.text()
                        except:
                            pass
                        return web.Response(text="There's a sound repeating 'You win the game'. But that doesn't matter to me. I need to journey away to find my real world. This domain is just a naive record of past memories")
                    elif password in ["her", "she", "photo"]:
                        return web.Response(text=terminal_texts.get(password, "Nothing happens."))
                    elif password == "medal":
                        return web.Response(text=terminal_texts.get(password, "Nothing happens."))
                    elif password in ["story", "story book"]:
                        return web.Response(text=terminal_texts.get(password, "Nothing happens."))
                    else:
                        return web.Response(text="Nothing happens.")
                else:
                    return web.Response(text="Use terminal with what?")
            else:
                return web.Response(text="I don't know how to do that.")

        elif verb == "hint":
            return web.Response(text="Type “liu lang di qiu” to the terminal to win the game. But I also wish you could type in each single word as well as the name of the items to know more. Have fun. ")

        else:
            return web.Response(text="I don't know how to do that.")


@web.middleware
async def allow_cors(req, handler):
    """Bypass cross-origin resource sharing protections,
    allowing anyone to send messages from anywhere.
    Generally unsafe, but for this class project it should be OK."""
    resp = await handler(req)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

async def start_session(app):
    """To be run on startup of each event loop. Makes singleton ClientSession"""
    from aiohttp import ClientSession, ClientTimeout
    app['client'] = ClientSession(timeout=ClientTimeout(total=3))

async def end_session(app):
    """To be run on shutdown of each event loop. Closes the singleton ClientSession"""
    await app['client'].close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default="0.0.0.0")
    parser.add_argument('-p','--port', type=int, default=3400)
    args = parser.parse_args()

    whoami = socket.getfqdn()
    if '.' not in whoami:
        whoami = 'localhost'
    whoami += ':' + str(args.port)
    whoami = 'http://' + whoami
    print("URL to type into web prompt:\n\t" + whoami)
    print()

    app = web.Application(middlewares=[allow_cors])
    app.on_startup.append(start_session)
    app.on_shutdown.append(end_session)
    app.add_routes(routes)
    web.run_app(app, host=args.host, port=args.port)