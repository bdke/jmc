"""Module containing JMCFunction subclasses for custom JMC function that can only be used on load function and used once"""

from ...exception import JMCMissingValueError
from ...datapack import DataPack
from ..utils import ArgType
from ..jmc_function import JMCFunction, FuncType, func_property


@func_property(
    func_type=FuncType.LOAD_ONCE,
    call_string="Player.firstJoin",
    arg_type={
        "function": ArgType.FUNC
    },
    name="player_first_join"
)
class PlayerFirstJoin(JMCFunction):
    def call(self) -> str:
        self.datapack.add_raw_private_function(
            self.name,
            [self.args["function"]],
            "main"
        )
        self.datapack.add_private_json("advancements", self.name, {
            "criteria": {
                "requirement": {
                    "trigger": "minecraft:tick"
                }
            },
            "rewards": {
                "function": f"{self.datapack.namespace}:{DataPack.private_name}/{self.name}/main"
            }
        })
        return ""


@func_property(
    func_type=FuncType.LOAD_ONCE,
    call_string="Player.rejoin",
    arg_type={
        "function": ArgType.FUNC
    },
    name="player_rejoin"
)
class PlayerRejoin(JMCFunction):
    obj = "__rejoin__"
    reset = f"scoreboard players set @s {obj} 0"

    def call(self) -> str:
        self.datapack.add_objective(
            self.obj, "custom:leave_game")
        self.datapack.add_tick_command(
            f'execute as @a[scores={{{self.obj}=1..}}] at @s run {self.datapack.call_func(self.name, "main")}')
        self.datapack.add_raw_private_function(
            self.name, [
                self.reset,
                self.args["function"]
            ], "main")
        return ""


@func_property(
    func_type=FuncType.LOAD_ONCE,
    call_string="Player.die",
    arg_type={
        "onDeath": ArgType.FUNC,
        "onRespawn": ArgType.FUNC
    },
    name="player_die",
    defaults={
        "onDeath": "",
        "onRespawn": ""
    }
)
class PlayerDie(JMCFunction):
    obj = "__die__"
    on_death = f"scoreboard players set @s {obj} 2"
    on_respawn = f"scoreboard players set @s {obj} 0"

    def call(self) -> str:
        if not self.args["onDeath"] and not self.args["onRespawn"]:
            raise JMCMissingValueError("onDeath or onRespawn",
                                       self.token, self.tokenizer)
        self.datapack.add_objective(self.obj, "deathCount")
        self.datapack.add_tick_command(
            f'execute as @a[scores={{{self.obj}=1..}}] at @s run {self.datapack.call_func(self.name, "on_death")}')
        self.datapack.add_tick_command(
            f'execute as @e[type=player,scores={{{self.obj}=2..}}] at @s run {self.datapack.call_func(self.name, "on_respawn")}')
        self.datapack.add_raw_private_function(
            self.name,
            [
                self.on_death,
                self.args["onDeath"],
            ],
            "on_death"
        )
        self.datapack.add_raw_private_function(
            self.name,
            [
                self.on_respawn,
                self.args["onRespawn"],
            ],
            "on_respawn"
        )
        return ""
