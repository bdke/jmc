"""Module containing JMCFunction subclasses for custom JMC function that can only be used on load function"""
from jmc.compile.utils import convention_jmc_to_mc
from ...tokenizer import Token, TokenType
from ...exception import JMCSyntaxException, JMCMissingValueError, JMCValueError
from ...datapack_data import GUI, GUIMode, Item
from ...datapack import DataPack
from ..utils import ArgType, NumberType, PlayerType, ScoreboardPlayer, FormattedText
from ..jmc_function import JMCFunction, FuncType, func_property
from .._flow_control import parse_switch


@func_property(
    func_type=FuncType.LOAD_ONLY,
    call_string="Predicate.locations",
    arg_type={
        "name": ArgType.STRING,
        "predicate": ArgType.JSON,
        "xMin": ArgType.INTEGER,
        "xMax": ArgType.INTEGER,
        "yMin": ArgType.INTEGER,
        "yMax": ArgType.INTEGER,
        "zMin": ArgType.INTEGER,
        "zMax": ArgType.INTEGER,
    },
    name="predicate_locations"
)
class PredicateLocations(JMCFunction):
    def call(self) -> str:
        predicates = []
        predicate = self.load_arg_json("predicate")
        for x in range(int(self.args["xMin"]), int(self.args["xMax"]) + 1):
            for y in range(int(self.args["yMin"]),
                           int(self.args["yMax"]) + 1):
                for z in range(int(self.args["zMin"]), int(
                        self.args["zMax"]) + 1):
                    predicates.append({
                        "condition": "minecraft:location_check",
                        "offsetX": x,
                        "offsetY": y,
                        "offsetZ": z,
                        "predicate": predicate
                    })

        self.datapack.add_json("predicate", self.args["name"], predicates)
        return ""


@func_property(
    func_type=FuncType.LOAD_ONLY,
    call_string="RightClick.setup",
    arg_type={
        "idName": ArgType.KEYWORD,
        "functionMap": ArgType.JS_OBJECT
    },
    name="right_click_setup"
)
class RightClickSetup(JMCFunction):
    tag_id_var = "__item_id__"

    def call(self) -> str:
        self.rc_obj = "__rc__" + self.args["idName"][:10]
        func_map = self.datapack.parse_func_map(
            self.raw_args["functionMap"].token, self.tokenizer)
        is_switch = sorted(func_map) == list(range(1, len(func_map) + 1))

        id_name = self.args["idName"]
        self.datapack.add_objective(self.rc_obj, "used:carrot_on_a_stick")
        if self.is_never_used():
            self.datapack.add_tick_command(
                f"""execute as @a[scores={{{self.rc_obj}=1..}}] at @s run {self.datapack.add_raw_private_function(self.name,
                                                       [f'scoreboard players set @s {self.rc_obj} 0'], 'main')}""")

        main_func = self.get_private_function("main")

        main_count = self.datapack.get_count(self.name)
        main_func.append(
            f"execute store result score {self.tag_id_var} {DataPack.var_name} run data get entity @s SelectedItem.tag.{id_name}")

        if is_switch:
            func_contents = []
            for func, is_arrow_func in func_map.values():
                if is_arrow_func:
                    func_contents.append(
                        [func]
                    )
                else:
                    func_contents.append(
                        [f"function {self.datapack.namespace}:{func}"])

            main_func.append(
                f"""execute if score {self.tag_id_var} {DataPack.var_name} matches 1.. run {parse_switch(ScoreboardPlayer(
                    PlayerType.SCOREBOARD, (self.tag_id_var, "@s")), func_contents, self.datapack, self.name)}""")
        else:
            main_func.append(
                f"execute if score {self.tag_id_var} {DataPack.var_name} matches 1.. run {self.datapack.call_func(self.name, main_count)}")
            run = []
            for num, (func, is_arrow_func) in func_map.items():
                if is_arrow_func:
                    run.append(
                        f'execute if score {self.tag_id_var} {DataPack.var_name} matches {num} at @s run {self.datapack.add_raw_private_function(self.name, [func])}')
                else:
                    run.append(
                        f'execute if score {self.tag_id_var} {DataPack.var_name} matches {num} at @s run function {self.datapack.namespace}:{func}')

            self.datapack.add_raw_private_function(self.name, run, main_count)

        return ""


@func_property(
    func_type=FuncType.LOAD_ONLY,
    call_string="Item.create",
    arg_type={
        "itemId": ArgType.KEYWORD,
        "itemType": ArgType.KEYWORD,
        "displayName": ArgType.STRING,
        "lore": ArgType.LIST,
        "nbt": ArgType.JS_OBJECT,
        "onClick": ArgType.FUNC
    },
    name="item_create",
    defaults={
        "lore": "",
        "nbt": "",
        "onClick": ""
    }
)
class ItemCreate(JMCFunction):
    rc_obj = {
        "carrot_on_a_stick": "__item_rc_carrot",
        "warped_fungus_on_a_stick": "__item_rc_warped"
    }
    tag_id_var = "__item_id__"
    id_name = "__item_id__"

    def call(self) -> str:
        modify_nbt = None
        item_type = self.args["itemType"]
        on_click = self.args["onClick"]
        if on_click and item_type not in {
                "carrot_on_a_stick", "warped_fungus_on_a_stick"}:
            raise JMCValueError(
                f'on_click can only be used with carrot_on_a_stick or warped_fungus_on_a_stick or in {self.call_string}',
                self.raw_args["onClick"].token,
                self.tokenizer,
                suggestion="Change item_type to carrot_on_a_stick or warped_fungus_on_a_stick")

        if on_click:
            rc_obj = self.rc_obj[self.args["itemType"]]
            item_id = self.datapack.data.get_item_id()
            self.datapack.add_objective(
                rc_obj, "used:" + self.args["itemType"])
            if self.is_never_used():
                self.datapack.add_tick_command(
                    f"""execute as @a[scores={{{rc_obj}=1..}}] at @s run {self.datapack.add_raw_private_function(self.name,
                                                       [
                                                        f'scoreboard players set @s {rc_obj} 0',
                                                        f"execute store result score {self.tag_id_var} {DataPack.var_name} run data get entity @s SelectedItem.tag.{self.id_name}",
                                                        f"execute if score {self.tag_id_var} {DataPack.var_name} matches 1.. run {self.datapack.call_func(self.name, 'found')}"
                                                        ], "main")}""")
                self.datapack.add_raw_private_function(self.name, [], "found")

            found_func = self.get_private_function("found")

            func = self.args["onClick"]

            if self.raw_args["onClick"].arg_type == ArgType.ARROW_FUNC:
                found_func.append(
                    f'execute if score {self.tag_id_var} {DataPack.var_name} matches {item_id} at @s run {self.datapack.add_raw_private_function(self.name, [func])}')
            else:
                found_func.append(
                    f'execute if score {self.tag_id_var} {DataPack.var_name} matches {item_id} at @s run {func}')

            modify_nbt = {self.id_name: Token.empty(item_id)}

        self.datapack.data.item[self.args["itemId"]
                                ] = self.create_item(modify_nbt=modify_nbt)

        return ""


@func_property(
    func_type=FuncType.LOAD_ONLY,
    call_string="Item.createSign",
    arg_type={
        "itemId": ArgType.KEYWORD,
        "variant": ArgType.KEYWORD,
        "displayName": ArgType.STRING,
        "lore": ArgType.LIST,
        "texts": ArgType.LIST,
        "nbt": ArgType.JS_OBJECT,
        "onClick": ArgType.FUNC
    },
    name="item_create_sign",
    defaults={
        "lore": "",
        "texts": "",
        "nbt": "",
        "onClick": ""
    }
)
class ItemCreateSign(JMCFunction):
    _variants = {"oak", "spruce", "birch", "jungle",
                 "acacia", "dark_oak", "crimson", "warped"}

    def call(self) -> str:
        variant = self.args["variant"]

        if variant not in self._variants:
            raise JMCValueError(
                f"Unrecognized wood variant for sign ({variant})",
                self.raw_args["variant"].token,
                self.tokenizer,
                suggestion=f"Available variants are {' '.join(repr(i) for i in self._variants)}")

        on_click = self.args["onClick"]
        name = self.args["displayName"]
        if self.args["lore"]:
            lores = self.datapack.parse_list(
                self.raw_args["lore"].token, self.tokenizer, TokenType.STRING)
        else:
            lores = []

        if self.args["texts"]:
            texts = self.datapack.parse_list(
                self.raw_args["texts"].token, self.tokenizer, TokenType.STRING)
        else:
            texts = []

        if len(texts) > 4:
            raise JMCValueError(
                f"Sign may only have 4 lines of text (got {len(texts)})",
                self.raw_args["texts"].token,
                self.tokenizer)
        texts.extend([''] * (4 - len(texts)))

        nbt = self.tokenizer.parse_js_obj(
            self.raw_args["nbt"].token) if self.args["nbt"] else {}

        if "display" in nbt:
            raise JMCValueError(
                "display is already inside the nbt",
                self.token,
                self.tokenizer)

        lore_ = ",".join(repr(str(FormattedText(lore, self.raw_args["lore"].token, self.tokenizer, self.datapack, is_default_no_italic=True, is_allow_score_selector=False)))
                         for lore in lores)
        formatted_texts_ = [FormattedText(text, self.raw_args["texts"].token, self.tokenizer, self.datapack) if text else FormattedText.empty(self.tokenizer, self.datapack)
                            for text in texts]
        if on_click:
            formatted_texts_[0].add_key(
                "clickEvent", {
                    "action": "run_command", "value": on_click})
            if not formatted_texts_[0]:
                formatted_texts_[0].add_key("text", "")

        texts_ = [repr(str(text)) for text in formatted_texts_]

        nbt["display"] = Token.empty(f"""{{Name:{repr(
            str(FormattedText(name, self.raw_args["displayName"].token, self.tokenizer, self.datapack, is_default_no_italic=True, is_allow_score_selector=False))
            )},Lore:[{lore_}]}},BlockEntityTag:{{Text1:{texts_[0]},Text2:{texts_[1]},Text3:{texts_[2]},Text4:{texts_[3]}}}""")

        self.datapack.data.item[self.args["itemId"]] = Item(
            variant + "_sign",
            self.datapack.token_dict_to_raw_js_object(nbt, self.tokenizer),
            nbt
        )

        return ""


@func_property(
    func_type=FuncType.LOAD_ONLY,
    call_string="Player.onEvent",
    arg_type={
        "criteria": ArgType.STRING,
        "function": ArgType.FUNC,
    },
    name="player_on_event"
)
class PlayerOnEvent(JMCFunction):
    def call(self) -> str:
        objective = f"on_event{self.datapack.get_count('on_event')}"
        if not self.is_never_used(parameters=[self.args['criteria']]):
            raise JMCValueError(
                f"{self.args['criteria']} criteria was already used.",
                self.raw_args["criteria"].token,
                self.tokenizer)
        self.datapack.add_load_command(
            f"scoreboard objectives add {objective} {self.args['criteria']}"
        )
        count = self.datapack.get_count(self.name)
        func = self.datapack.add_raw_private_function(
            self.name, [f"scoreboard players set @s {objective} 0", self.args['function']], count=count)
        self.datapack.add_tick_command(
            f"execute as @a[scores={{{objective}=1..}}] at @s run {func}")
        return ""


@func_property(
    func_type=FuncType.LOAD_ONLY,
    call_string="Trigger.setup",
    arg_type={
        "objective": ArgType.KEYWORD,
        "triggers": ArgType.JS_OBJECT
    },
    name="trigger_setup",
    ignore={
        "triggers"
    }
)
class TriggerSetup(JMCFunction):
    def call(self) -> str:
        func_map = self.datapack.parse_func_map(
            self.raw_args["triggers"].token, self.tokenizer)
        is_switch = sorted(func_map) == list(range(1, len(func_map) + 1))

        obj = self.args["objective"]
        self.datapack.add_objective(obj, "trigger")
        if self.is_never_used():
            self.datapack.add_tick_command(
                self.datapack.call_func(self.name, "main"))
            self.make_empty_private_function("main")
            self.datapack.add_load_command(
                f"execute as @a run {self.datapack.call_func(self.name, 'enable')}")
            self.make_empty_private_function("enable")

            self.datapack.add_private_json("advancements", f"{self.name}/enable", {
                "criteria": {
                    "requirement": {
                        "trigger": "minecraft:tick"
                    }
                },
                "rewards": {
                    "function": f"{self.datapack.namespace}:{DataPack.private_name}/{self.name}/enable"
                }
            })

        main_func = self.get_private_function("main")
        self.get_private_function("enable").append(
            f"scoreboard players enable @s {obj}")

        main_count = self.datapack.get_count(self.name)
        main_func.append(
            f"execute as @a[scores={{{obj}=1..}}] at @s run {self.datapack.call_func(self.name, main_count)}")

        if is_switch:
            func_contents = []
            for func, is_arrow_func in func_map.values():
                if is_arrow_func:
                    func_contents.append(
                        [func]
                    )
                else:
                    func_contents.append(
                        [f"function {self.datapack.namespace}:{func}"])
            run = [
                parse_switch(ScoreboardPlayer(
                    PlayerType.SCOREBOARD, (obj, "@s")), func_contents, self.datapack, self.name),
            ]
        else:
            run = []
            for num, (func, is_arrow_func) in func_map.items():
                if is_arrow_func:
                    run.append(
                        f'execute if score @s {obj} {DataPack.var_name} matches {num} run {self.datapack.add_raw_private_function(self.name, [func])}')
                else:
                    run.append(
                        f'execute if score @s {obj} {DataPack.var_name} matches {num} run {func}')

        run.extend([f"scoreboard players set @s {obj} 0",
                    f"scoreboard players enable @s {obj}"])
        self.datapack.add_raw_private_function(self.name, run, main_count)

        return ""


@func_property(
    func_type=FuncType.LOAD_ONLY,
    call_string="Trigger.add",
    arg_type={
        "objective": ArgType.KEYWORD,
        "function": ArgType.FUNC
    },
    name="trigger_add",
)
class TriggerAdd(JMCFunction):
    def call(self) -> str:

        obj = self.args["objective"]
        self.datapack.add_objective(obj, "trigger")
        if self.is_never_used():
            self.datapack.add_tick_command(
                self.datapack.call_func(self.name, "main"))
            self.make_empty_private_function("main")
            self.datapack.add_load_command(
                f"execute as @a run {self.datapack.call_func(self.name, 'enable')}")
            self.make_empty_private_function("enable")

            self.datapack.add_private_json("advancements", f"{self.name}/enable", {
                "criteria": {
                    "requirement": {
                        "trigger": "minecraft:tick"
                    }
                },
                "rewards": {
                    "function": f"{self.datapack.namespace}:{DataPack.private_name}/{self.name}/enable"
                }
            })

        main_func = self.get_private_function("main")
        self.get_private_function("enable").append(
            f"scoreboard players enable @s {obj}")

        func = self.args["function"]
        run = f"""execute as @a[scores={{{obj}=1..}}] at @s run {self.datapack.add_raw_private_function(self.name, [
                func,
                f"scoreboard players set @s {obj} 0",
                f"scoreboard players enable @s {obj}"
                ], obj)}"""
        main_func.append(run)

        return ""


@ func_property(
    func_type=FuncType.LOAD_ONLY,
    call_string="Timer.add",
    arg_type={
        "objective": ArgType.KEYWORD,
        "mode": ArgType.KEYWORD,
        "selector": ArgType.SELECTOR,
        "function": ArgType.FUNC
    },
    name="timer_add",
    defaults={
        "function": ""
    }
)
class TimerAdd(JMCFunction):
    def call(self) -> str:
        mode = self.args["mode"]
        obj = self.args["objective"]
        selector = self.args["selector"]
        if mode not in {"runOnce", "runTick", "none"}:
            raise JMCSyntaxException(
                f"Avaliable modes for {self.call_string} are 'runOnce', 'runTick' and 'none' (got '{mode}')", self.raw_args["mode"].token, self.tokenizer, suggestion="'runOnce' run the commands once after the timer is over.\n'runTick' run the commands every tick if timer is over.\n'none' do not run any command.")

        if mode in {"runOnce",
                    "runTick"} and self.raw_args["function"] is None:
            raise JMCMissingValueError("function", self.token, self.tokenizer)
        if mode == "none" and self.raw_args["function"] is not None:
            raise JMCSyntaxException(
                f"'function' is provided in 'none' mode {self.call_string}", self.raw_args["function"].token, self.tokenizer)
        self.datapack.add_objective(obj)
        if self.is_never_used():
            self.datapack.add_tick_command(
                self.datapack.call_func(self.name, "main"))
            self.make_empty_private_function("main")

        main_func = self.get_private_function("main")
        if selector.startswith("@"):
            if_selector = f"as {selector} if score @s"
            unless_selector = f"as {selector} unless score @s"
            at_s = "@s"
            at_at_s = "at @s "
        else:
            if_selector = f"if score {selector}"
            unless_selector = f"unless score {selector}"
            at_s = selector
            at_at_s = ""
        main_func.append(
            f"execute {if_selector} {obj} matches 0.. run scoreboard players remove {at_s} {obj} 1")
        if mode == "runOnce":
            count = self.datapack.get_count(self.name)
            main_func.append(
                f"""execute {if_selector} {obj} matches 0 {at_at_s}run {self.datapack.add_raw_private_function(
                    self.name,
                    [
                        f"scoreboard players set {at_s} {obj} 0",
                        self.args["function"]
                    ],
                    count
                )}""")
        elif mode == "runTick":
            count = self.datapack.get_count(self.name)
            main_func.append(
                f"""execute {unless_selector} {obj} matches 1.. {at_at_s}run {self.datapack.add_raw_private_function(
                    self.name,
                    [self.args["function"]],
                    count
                )}""")

        return ""


@func_property(
    func_type=FuncType.LOAD_ONLY,
    call_string="Recipe.table",
    arg_type={
        "recipe": ArgType.JSON,
        "baseItem": ArgType.KEYWORD,
        "onCraft": ArgType.FUNC
    },
    name="recipe_table",
    defaults={
        "baseItem": "minecraft:knowledge_book",
        "onCraft": ""
    }
)
class RecipeTable(JMCFunction):
    def call(self) -> str:
        base_item = self.args["baseItem"]
        if not base_item.startswith("minecraft:"):
            base_item = "minecraft:" + base_item
        count = self.datapack.get_count(self.name)
        self.datapack.add_private_json('advancements', f'{self.name}/{count}', {
            "criteria": {
                "requirement": {
                    "trigger": "minecraft:recipe_unlocked",
                    "conditions": {
                        "recipe": f"{self.datapack.namespace}:{DataPack.private_name}/{self.name}/{count}"
                    }
                }
            },
            "rewards": {
                "function": f"{self.datapack.namespace}:{DataPack.private_name}/{self.name}/{count}"
            }
        })

        json = self.load_arg_json("recipe")

        # raise JMCSyntaxException("'result' key not found in recipe",
        # self.raw_args["recipe"].token, self.tokenizer,
        # display_col_length=True, suggestion="recipe json maybe invalid")
        if "result" in json:
            if "item" not in json["result"]:
                raise JMCSyntaxException("'item' key not found in 'result' in recipe",
                                         self.raw_args["recipe"].token, self.tokenizer, display_col_length=True, suggestion="recipe json maybe invalid")
            if "count" not in json["result"]:
                raise JMCSyntaxException("'count' key not found in 'result' in recipe",
                                         self.raw_args["recipe"].token, self.tokenizer, display_col_length=True, suggestion="recipe json maybe invalid")

            result_item = json["result"]["item"]
            json["result"]["item"] = base_item
            result_count = json["result"]["count"]
            json["result"]["count"] = 1
            result_command = f"give @s {result_item} {result_count}"
        else:
            result_command = ""

        self.datapack.add_private_json(
            "recipes", f"{self.name}/{count}", json)
        self.datapack.add_raw_private_function(
            self.name,
            [
                f"clear @s {base_item} 1",
                result_command,
                f"recipe take @s {self.datapack.namespace}:{DataPack.private_name}/{self.name}/{count}",
                f"advancement revoke @s only {self.datapack.namespace}:{DataPack.private_name}/{self.name}/{count}",
                self.args["onCraft"]
            ],
            count
        )
        return ""


GUI_OBJ_NAME = "__gui__"


@func_property(
    func_type=FuncType.LOAD_ONLY,
    call_string="GUI.template",
    arg_type={
        "name": ArgType.KEYWORD,
        "template": ArgType.LIST,
        "mode": ArgType.KEYWORD
    },
    name="gui_template"
)
class GUITemplate(JMCFunction):
    MODE_MAP: dict[str, GUIMode] = {
        "entity": GUIMode.ENTITY,
        "block": GUIMode.BLOCK,
        "enderchest": GUIMode.ENDERCHEST
    }

    def call(self) -> str:
        template = self.datapack.parse_list(
            self.raw_args["template"].token, self.tokenizer, TokenType.STRING)
        name = convention_jmc_to_mc(
            self.raw_args["name"].token, self.tokenizer)
        mode_str = self.args["mode"]
        if mode_str not in self.MODE_MAP:
            raise JMCValueError(
                f"Unrecognized mode for {self.call_string}",
                self.raw_args["mode"].token,
                self.tokenizer,
                suggestion=f"""Available modes are {', '.join("'"+mode_+"'" for mode_ in self.MODE_MAP.keys())}""")
        if name in self.datapack.data.guis:
            raise JMCValueError(
                f"GUI Template '{name}' was already defined",
                self.raw_args["name"].token,
                self.tokenizer)
        mode = self.MODE_MAP[mode_str]
        self.datapack.data.guis[name] = GUI(
            name, mode, template)
        if self.is_never_used():
            self.datapack.add_load_command(
                f"data modify storage {self.datapack.namespace}:{self.datapack.storage_name} GUI set value {{}}")
        self.datapack.add_raw_private_function(f"gui/{name}", [
            f"""execute if entity @p[distance=..8] run {
                self.datapack.add_raw_private_function(f"gui/{name}", [
                    f"data modify storage {self.datapack.namespace}:{self.datapack.storage_name} GUI.Items set from {mode.value[1]} {mode.value[2]}",
                    f"execute store result score __gui__.item_count {self.datapack.var_name} if data storage {self.datapack.namespace}:{self.datapack.storage_name} GUI.Items[].tag.__gui__",
                    f'execute if score __gui__.item_count {self.datapack.var_name} matches 0 run {self.datapack.call_func(f"gui/{name}", "reset")}'
                ], "active")
                }""",
            "execute if block ~ ~-1 ~ hopper run data merge block ~ ~-1 ~ {TransferCooldown:20d}" if mode ==
            GUIMode.BLOCK else ""
        ], "run")
        self.datapack.add_raw_private_function(
            f"gui/{name}", [
                f"scoreboard players reset * {GUI_OBJ_NAME}"
            ], "container_changed")

        return ""


@func_property(
    func_type=FuncType.LOAD_ONLY,
    call_string="GUI.registers",
    arg_type={
        "name": ArgType.KEYWORD,
        "id": ArgType.STRING,
        "items": ArgType.LIST,
        "variable": ArgType.SCOREBOARD,
        "onClick": ArgType.FUNC,
        "onClickAsGUI": ArgType.FUNC
    },
    name="gui_registers",
    defaults={
        "onClick": "",
        "onClickAsGUI": ""
    }
)
class GUIRegisters(JMCFunction):
    def call(self) -> str:
        name = convention_jmc_to_mc(
            self.raw_args["name"].token, self.tokenizer)
        if name not in self.datapack.data.guis:
            raise JMCValueError(
                f"GUI Template '{name}' was never defined",
                self.raw_args["name"].token,
                self.tokenizer)

        if len(self.args["id"]) != 1:
            raise JMCValueError(
                f"'id' expected 1 charater (got {len(self.args['id'])})",
                self.raw_args["id"].token,
                self.tokenizer)

        item_strings = self.datapack.parse_list(self.raw_args["items"].token,
                                                self.tokenizer, TokenType.KEYWORD)

        items: list[Item] = []

        if self.args["onClick"]:
            on_click = self.datapack.add_private_function(
                f"gui/{name}/on_click", self.args["onClick"])
            interactive_id = self.datapack.get_count(
                f"{self.name}/{name}")
            for item_str in item_strings:
                if item_str not in self.datapack.data.item:
                    raise JMCValueError(
                        f'Item id: \'{item_str}\' is not defined.',
                        self.raw_args["items"].token,
                        self.tokenizer,
                        suggestion=f"Use Item.create to make this item BEFORE using {self.call_string}"
                    )
                items.append(self.create_new_item(self.datapack.data.item[item_str], modify_nbt={
                    "__gui__": Token.empty(f"{{interactive_id:{interactive_id},name:{repr(name)}}}")}))

            self.set_items(
                name,
                self.args["id"],
                items,
                self.raw_args["id"].token,
                interactive_id,
                on_click)
        else:
            for item_str in item_strings:
                if item_str not in self.datapack.data.item:
                    raise JMCValueError(
                        f'Item id: \'{item_str}\' is not defined.',
                        self.raw_args["items"].token,
                        self.tokenizer,
                        suggestion=f"Use Item.create to make this item BEFORE using {self.call_string}"
                    )
                items.append(self.create_new_item(self.datapack.data.item[item_str], modify_nbt={
                    "__gui__": Token.empty(f"{{name:{repr(name)}}}")}))
            self.set_items(
                name,
                self.args["id"],
                items,
                self.raw_args["id"].token)

        return ""

    def set_items(self, name: str, slot: str, items: list[Item], token: Token,
                  interactive_id: str | None = None, on_click: str = "") -> None:
        gui = self.datapack.data.guis[name]
        for item in items:
            if item.item_type == "air":
                raise JMCValueError(
                    f"Item cannot be air",
                    token,
                    self.tokenizer)
            gui.item_types.add(item.item_type)

        for template_item in gui.template_map[slot]:
            if template_item.items is not gui.default_item:
                raise JMCValueError(
                    f"This id ({slot}) was already registered in {name} template",
                    token,
                    self.tokenizer)
            if template_item.variable is not None:
                raise JMCValueError(
                    f"This id ({slot}) was already registered as registers in {name} template",
                    self.raw_args["id"].token,
                    self.tokenizer)
            template_item.items = items
            template_item.interactive_id = interactive_id
            template_item.on_click = on_click
            template_item.variable = self.args["variable"]
            if self.args["onClickAsGUI"]:
                template_item.container_changed = [self.args["onClickAsGUI"]]


@func_property(
    func_type=FuncType.LOAD_ONLY,
    call_string="GUI.register",
    arg_type={
        "name": ArgType.KEYWORD,
        "id": ArgType.STRING,
        "item": ArgType.KEYWORD,
        "displayName": ArgType.STRING,
        "lore": ArgType.LIST,
        "nbt": ArgType.JS_OBJECT,
        "onClick": ArgType.FUNC,
        "onClickAsGUI": ArgType.FUNC
    },
    name="gui_register",
    defaults={
        "displayName": "",
        "lore": "",
        "nbt": "",
        "onClick": "",
        "onClickAsGUI": ""
    }
)
class GUIRegister(JMCFunction):
    def call(self) -> str:
        name = convention_jmc_to_mc(
            self.raw_args["name"].token, self.tokenizer)
        if name not in self.datapack.data.guis:
            raise JMCValueError(
                f"GUI Template '{name}' was never defined",
                self.raw_args["name"].token,
                self.tokenizer)

        if len(self.args["id"]) != 1:
            raise JMCValueError(
                f"'id' expected 1 charater (got {len(self.args['id'])})",
                self.raw_args["id"].token,
                self.tokenizer)
        if self.args["onClick"]:
            on_click = self.datapack.add_private_function(
                f"gui/{name}/on_click", self.args["onClick"])
            interactive_id = self.datapack.get_count(
                f"{self.name}/{name}")

            self.set_item(
                name,
                self.args["id"],
                self.create_item(
                    item_type_param="item",
                    modify_nbt={"__gui__": Token.empty(f"{{interactive_id:{interactive_id},name:{repr(name)}}}")}),
                self.raw_args["id"].token,
                interactive_id,
                on_click)

        else:
            self.set_item(
                name,
                self.args["id"],
                self.create_item(
                    item_type_param="item",
                    modify_nbt={"__gui__": Token.empty(f"{{name:{repr(name)}}}")}),
                self.raw_args["id"].token)

        return ""

    def set_item(self, name: str, slot: str, item: Item, token: Token,
                 interactive_id: str | None = None, on_click: str = "") -> None:
        gui = self.datapack.data.guis[name]
        if item.item_type != "air":
            gui.item_types.add(item.item_type)
        for template_item in gui.template_map[slot]:
            if template_item.items is not gui.default_item:
                raise JMCValueError(
                    f"This id ({slot}) was already registered in {name} template",
                    token,
                    self.tokenizer)
            if template_item.variable is not None:
                raise JMCValueError(
                    f"This id ({slot}) was already registered as registers in {name} template",
                    self.raw_args["id"].token,
                    self.tokenizer)
            template_item.items = item if item.item_type != "air" else None
            template_item.interactive_id = interactive_id
            template_item.on_click = on_click
            if self.args["onClickAsGUI"]:
                template_item.container_changed = [self.args["onClickAsGUI"]]


@func_property(
    func_type=FuncType.LOAD_ONLY,
    call_string="GUI.create",
    arg_type={
        "name": ArgType.KEYWORD,
    },
    name="gui_create"
)
class GUICreate(JMCFunction):

    def call(self) -> str:
        name = convention_jmc_to_mc(
            self.raw_args["name"].token, self.tokenizer)
        if name not in self.datapack.data.guis:
            raise JMCValueError(
                f"GUI Template '{name}' was never defined",
                self.raw_args["name"].token,
                self.tokenizer)

        if self.is_never_used():
            self.datapack.add_objective(GUI_OBJ_NAME)
            self.datapack.add_raw_private_function("__gui__", [
                f"execute store result score $UUID0_P {GUI_OBJ_NAME} run data get entity @s UUID[0]",
                f"execute store result score $UUID1_P {GUI_OBJ_NAME} run data get entity @s UUID[1]",
                f"execute store result score $UUID2_P {GUI_OBJ_NAME} run data get entity @s UUID[2]",
                f"execute store result score $UUID3_P {GUI_OBJ_NAME} run data get entity @s UUID[3]",
                f"execute if score $UUID0_P {GUI_OBJ_NAME} = $UUID0_E {GUI_OBJ_NAME} if score $UUID1_P {GUI_OBJ_NAME} = $UUID1_E {GUI_OBJ_NAME} if score $UUID2_P {GUI_OBJ_NAME} = $UUID2_E {GUI_OBJ_NAME} if score $UUID3_P {GUI_OBJ_NAME} = $UUID3_E {GUI_OBJ_NAME} run tag @s add __gui__.clicker"
            ], "compare_player_uuid")

            self.datapack.add_raw_private_function("__gui__", [
                f"execute store result score $UUID0_E {GUI_OBJ_NAME} run data get entity @s Thrower[0]",
                f"execute store result score $UUID1_E {GUI_OBJ_NAME} run data get entity @s Thrower[1]",
                f"execute store result score $UUID2_E {GUI_OBJ_NAME} run data get entity @s Thrower[2]",
                f"execute store result score $UUID3_E {GUI_OBJ_NAME} run data get entity @s Thrower[3]",
            ], "copy_item_owner")

            self.datapack.add_raw_private_function(
                f"__gui__", [
                    f"data modify entity @s Owner set from entity @p[tag=__gui__.clicker] UUID",
                    f"tp @s @p[tag=__gui__.clicker]"
                ], "return_item"
            )

        return_item = self.datapack.call_func("__gui__", "return_item")
        copy_item_owner = self.datapack.call_func("__gui__", "copy_item_owner")
        compare_player_uuid = self.datapack.call_func(
            "__gui__", "compare_player_uuid")

        container_changed = self.datapack.private_functions[f"gui/{name}"]["container_changed"]
        gui = self.datapack.data.guis[name]
        if gui.is_created:
            raise JMCValueError(
                f"GUI '{name}' was already created",
                self.raw_args["name"].token,
                self.tokenizer)
        gui.is_created = True

        self.datapack.private_functions[f"gui/{name}"]["active"].append(
            f'execute unless score __gui__.item_count {self.datapack.var_name} matches 0 unless score __gui__.item_count {self.datapack.var_name} matches {gui.length} run {self.datapack.call_func(f"gui/{name}", "container_changed")}')
        self.datapack.add_private_json(
            "tags/items", f"gui/{name}", {"values": list(gui.item_types)})
        item_tags = f"#{self.datapack.namespace}:{self.datapack.private_name}/gui/{name}"

        reset_commands = gui.get_reset_commands()
        reset_commands.append("kill @e[type=minecraft:item,nbt={Item:{tag:{__gui__:{name:%s}}}}]" % repr(
            name),)
        reset = self.datapack.add_raw_private_function(
            f"gui/{name}", reset_commands, "reset")

        for index, template_item in enumerate(gui.template):
            if template_item.items is None:
                continue
            on_change = self.datapack.add_raw_private_function(
                f"gui/{name}/container_changed", [
                    f"execute store result score $is_item {GUI_OBJ_NAME} if data storage {self.datapack.namespace}:{self.datapack.storage_name} GUI.Items[{{Slot:{index}b}}]",
                    # Find player with gui item
                    f'execute as @a[distance=..10] store result score @s {GUI_OBJ_NAME} run clear @s {item_tags}{{__gui__:{{name:{repr(name)}}}}}',
                    # Tag player with gui item as clicker
                    f"tag @p[scores={{{GUI_OBJ_NAME}=1..}}] add __gui__.clicker",
                    # Check if clicker is found
                    f"execute if entity @p[tag=__gui__.clicker] run scoreboard players set $is_click {GUI_OBJ_NAME} 1",
                    # If there's no clicker
                    "execute unless score $is_click %s matches 1 as @e[type=item,nbt={Item:{tag:{__gui__:{name:%s}}}},limit=1] run %s" % (
                        GUI_OBJ_NAME, repr(name), copy_item_owner),
                    f"execute unless score $is_click {GUI_OBJ_NAME} matches 1 as @a[distance=..8] run {compare_player_uuid}",
                    # Summon dummy item
                    'execute if score $is_item %s matches 1 run summon item ~ ~256 ~ {Item: {id:"minecraft:stone",Count:1b},Tags:["__gui__.%s.dropped_item"]}' % (
                        GUI_OBJ_NAME, name),
                    f"data modify entity @e[limit=1,type=item,tag=__gui__.{name}.dropped_item] Item set from storage {self.datapack.namespace}:{self.datapack.storage_name} GUI.Items[{{Slot:{index}b}}]",
                    f"execute if score $is_item {GUI_OBJ_NAME} matches 1 as @e[limit=1,type=item,tag=__gui__.{name}.dropped_item] run {return_item}",
                    f"""execute as @p[tag=__gui__.clicker] at @s run {template_item.on_click}""" if template_item.interactive_id is not None else "",
                    *template_item.container_changed
                ])
            container_changed.append(
                f"execute unless data storage {self.datapack.namespace}:{self.datapack.storage_name} GUI.Items[{{Slot:{index}b,tag:{{__gui__:{{name:{repr(name)}}}}}}}] run {on_change}")

        container_changed.extend([
            "kill @e[type=minecraft:item,nbt={Item:{tag:{__gui__:{name:%s}}}}]" % repr(
                name),
            "tag @a remove __gui__.clicker",
            reset])

        return ""


# @ func_property(
#     func_type=FuncType.load_only,
#     call_string='Debug.track',
#     arg_type={},
#     name='debug_track'
# )
# class DebugTrack(JMCFunction):
#     pass


# @ func_property(
#     func_type=FuncType.load_only,
#     call_string='Debug.history',
#     arg_type={},
#     name='debug_history'
# )
# class DebugHistory(JMCFunction):
#     pass


# @ func_property(
#     func_type=FuncType.load_only,
#     call_string='Debug.cleanup',
#     arg_type={},
#     name='debug_cleanup'
# )
# class DebugCleanup(JMCFunction):
#     pass
