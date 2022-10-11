import sys  # noqa
sys.path.append('./src')  # noqa

import unittest
from tests.utils import string_to_tree_dict
from jmc.test_compile import JMCPack

from jmc.exception import JMCMissingValueError, JMCValueError

class TestVarOperation(unittest.TestCase):
    def test_MathSqrt(self):
        pack = JMCPack().set_jmc_file("""
$i = Math.sqrt($x);
$i = Math.sqrt($i);
        """).build()

        self.assertDictEqual(
            pack.built,
            string_to_tree_dict("""
> VIRTUAL/data/minecraft/tags/functions/load.json
{
  "values": [
    "TEST:__load__"
  ]
}
> VIRTUAL/data/TEST/functions/__load__.mcfunction
scoreboard objectives add __variable__ dummy
scoreboard objectives add __int__ dummy
scoreboard players set 2 __int__ 2
scoreboard players operation __math__.N __variable__ = $x __variable__
function TEST:__private__/math_sqrt/main
scoreboard players operation $i __variable__ = __math__.x_n __variable__
scoreboard players operation __math__.N __variable__ = $i __variable__
function TEST:__private__/math_sqrt/main
scoreboard players operation $i __variable__ = __math__.x_n __variable__
> VIRTUAL/data/TEST/functions/__private__/math_sqrt/newton_raphson.mcfunction
scoreboard players operation __math__.x __variable__ = __math__.x_n __variable__
scoreboard players operation __math__.x_n __variable__ = __math__.N __variable__
scoreboard players operation __math__.x_n __variable__ /= __math__.x __variable__
scoreboard players operation __math__.x_n __variable__ += __math__.x __variable__
scoreboard players operation __math__.x_n __variable__ /= 2 __int__
scoreboard players operation __math__.different __variable__ = __math__.x __variable__
scoreboard players operation __math__.different __variable__ -= __math__.x_n __variable__
execute unless score __math__.different __variable__ 0..1 run function TEST:__private__/math_sqrt/newton_raphson
> VIRTUAL/data/TEST/functions/__private__/math_sqrt/main.mcfunction
scoreboard players set __math__.x_n __variable__ 1225
function TEST:__private__/math_sqrt/newton_raphson
scoreboard players operation __main__.x_n_sq __variable__ = __math__.x_n __variable__
scoreboard players operation __main__.x_n_sq __variable__ *= __math__.x_n __variable__
scoreboard players operation __math__.x_n __variable__ /= 2 __int__
scoreboard players operation __math__.different __variable__ = __math__.x __variable__
scoreboard players operation __math__.different __variable__ -= __math__.x_n __variable__
execute if score __main__.x_n_sq __variable__ > __math__.N __variable__ run scoreboard players remove __math__.x_n __variable__ 1
            """)
        )

        with self.assertRaises(JMCMissingValueError):
            JMCPack().set_jmc_file("""
$x = Math.sqrt();
        """).build()

        with self.assertRaises(JMCValueError):
            JMCPack().set_jmc_file("""
$x = Math.sqrt(10);
        """).build()

    def test_MathRandom(self):
        pack = JMCPack().set_jmc_file("""
$x = Math.random();
$y = Math.random(min=5, max=10);
$z = Math.random(max=10);
        """).build()

        self.assertDictEqual(
            pack.built,
            string_to_tree_dict("""
> VIRTUAL/data/minecraft/tags/functions/load.json
{
  "values": [
    "TEST:__load__"
  ]
}
> VIRTUAL/data/TEST/functions/__load__.mcfunction
scoreboard objectives add __variable__ dummy
scoreboard objectives add __int__ dummy
scoreboard players set 10 __int__ 10
scoreboard players set 6 __int__ 6
scoreboard players set 2147483647 __int__ 2147483647
execute unless score __math__.seed __variable__ matches -2147483648..2147483647 run function TEST:__private__/math_random/setup
function TEST:__private__/math_random/main
scoreboard players operation $x __variable__ = __math__.seed __variable__
scoreboard players operation $x __variable__ %= 2147483647 __int__
scoreboard players add $x __variable__ 1
function TEST:__private__/math_random/main
scoreboard players operation $y __variable__ = __math__.seed __variable__
scoreboard players operation $y __variable__ %= 6 __int__
scoreboard players add $y __variable__ 5
function TEST:__private__/math_random/main
scoreboard players operation $z __variable__ = __math__.seed __variable__
scoreboard players operation $z __variable__ %= 10 __int__
scoreboard players add $z __variable__ 1
> VIRTUAL/data/TEST/functions/__private__/math_random/setup.mcfunction
execute store result score __math__.seed __variable__ run loot spawn ~ ~ ~ loot TEST:__private__/math_random/rng
execute store result score __math__.rng.a __variable__ run loot spawn ~ ~ ~ loot TEST:__private__/math_random/rng
scoreboard players operation __math__.rng.a __variable__ *= __math__.rng.a __variable__
execute store result score __math__.rng.c __variable__ run loot spawn ~ ~ ~ loot TEST:__private__/math_random/rng
scoreboard players operation __math__.rng.c __variable__ *= __math__.rng.c __variable__
> VIRTUAL/data/TEST/functions/__private__/math_random/main.mcfunction
scoreboard players operation __math__.seed __variable__ *= __math__.rng.a __variable__
scoreboard players operation __math__.seed __variable__ += __math__.rng.c __variable__
> VIRTUAL/data/TEST/loot_tables/__private__/math_random/rng.json
{
  "pools": [
    {
      "rolls": {
        "min": 1,
        "max": 2147483647
      },
      "entries": [
        {
          "type": "minecraft:item",
          "name": "minecraft:stone",
          "functions": [
            {
              "function": "minecraft:set_count",
              "count": 0
            }
          ]
        }
      ]
    }
  ]
}
            """)
        )

        with self.assertRaises(JMCValueError):
            JMCPack().set_jmc_file("""
$x = Math.random(min=100,max=1);
        """).build()


class TestBoolFunction(unittest.TestCase):
    def test_TimerIsOver(self): ...


class TestExecuteExcluded(unittest.TestCase):
    def test_error_execute(self): ...
    def test_HardcodeRepeat(self): ...
    def test_HardcodeSwitch(self): ...


class TestJMCCommand(unittest.TestCase):
    def test_TimerSet(self): ...
    def test_ParticleCircle(self): ...
    def test_ParticleSpiral(self): ...
    def test_ParticleCylinder(self): ...


class TestLoadOnce(unittest.TestCase):
    def test_error_load_twice(self): ...
    def test_error_no_load(self): ...
    def test_PlayerFirstJoin(self): ...
    def test_PlayerRejoin(self): ...
    def test_PlayerDie(self): ...


class TestLoadOnly(unittest.TestCase):
    def test_error_no_load(self): ...
    def test_RightClickSetup(self): ...
    def test_PlayerOnEvent(self): ...
    def test_TriggerSetup(self): ...
    def test_TimerAdd(self): ...
    def test_RecipeTable(self): ...


if __name__ == '__main__':
    unittest.main()