"""Module handling datapack"""
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Iterable
from json import JSONEncoder, dumps


from .tokenizer import Token, TokenType, Tokenizer
from .datapack_data import Data
from .exception import JMCSyntaxWarning, JMCValueError
from .log import Logger

if TYPE_CHECKING:
    from .lexer import Lexer
    from .header import Header

logger = Logger(__name__)


NEW_LINE = "\n"


class FunctionEncoder(JSONEncoder):
    """
    Custom minecraft function encoder for json.dump
    """

    def default(self, o):
        if isinstance(o, Function):
            return o.commands
        return super().default(o)


class Function:
    """
    A class representation for a minecraft function (.mcfunction)

    :param commands: List of minecraft commands(string), defaults to empty list
    """
    __slots__ = ("commands", )
    commands: list[str]

    def __init__(self, commands: list[str] | None = None) -> None:
        if commands is None:
            self.commands = []
        else:
            self.commands = self.__split(commands)

    def add_empty_line(self) -> None:
        """
        Add empty line at the end of the function
        """
        self.commands.append('')

    def append(self, command: str) -> None:
        """
        Append 1 or more command in form of a single string

        :param command: 1 or more line of minecraft command string
        """
        self.commands.extend(self.__split([command]))

    def extend(self, commands: list[str]) -> None:
        """
        Append multiple minecraft commands

        :param commands: List of minecraft commands(strings), each string can have multiple lines
        """
        self.commands.extend(self.__split(commands))

    def insert_extend(self, commands: list[str], index: int) -> None:
        """
        Append multiple minecraft commands to a certine line of function

        :param commands:  List of minecraft commands(strings), each string can have multiple lines
        :param index: Line/Position of the function to insert to
        """
        self.commands[index:index] = self.__split(commands)

    def delete(self, index: int) -> None:
        """
        Delete a command

        :param index: Line/Position of the function to delete
        """
        del self.commands[index]

    @property
    def content(self) -> str:
        """
        Content of the function in 1 string

        :return: Commands of the function in form of a single string
        """
        return "\n".join(self.commands)

    @property
    def length(self) -> int:
        """
        Amount of lines in the function (including empty lines)

        :return: Length of commands attribute
        """
        return len(self.commands)

    def __repr__(self) -> str:
        return f"Function({repr(self.commands)})"

    def __iter__(self) -> Iterable:
        return self.commands.__iter__()

    def __bool__(self):
        return bool(self.commands)

    def __split(self, strings: list[str]) -> list[str]:
        """
        Loop through every line in each string of command(s) and make a new list with every element having only 1 line of command

        :param strings: minecraft commands(strings),each string can have multiple lines
        :return: minecraft commands(strings),each string can have only a single line
        """
        return [
            line for string in strings for line in string.split("\n") if line]


class DataPack:
    """
    A class representation for entire minecraft datapack

    :param namespace: Datapack's namespace
    :param lexer: Lexer object
    """
    __slot__ = ("data", "ints",
                "functions", "load_function", "jsons",
                "private_functions", "private_function_count",
                "__scoreboards", "loads", "ticks", "namespace",
                "used_command", "lexer", "defined_file_pos")
    private_name = "__private__"
    load_name = "__load__"
    tick_name = "__tick__"
    var_name = "__variable__"
    int_name = "__int__"
    storage_name = "__storage__"
    VARIABLE_SIGN = "$"
    """Data read from header file(s)"""

    def __init__(self, namespace: str, lexer: "Lexer") -> None:
        logger.debug("Initializing Datapack")
        self.ints: set[int] = set()
        """Set of integers going to be used in scoreboard"""
        self.functions: dict[str, Function] = {}
        """Dictionary of function name and a Function object"""
        self.load_function: list[list[Token]] = []
        """List of commands(list of tokens) in load function"""
        self.jsons: dict[str, dict[str, Any] | list[Any]] = defaultdict(dict)
        """Dictionary of json name and a dictionary(jsobject)"""
        self.private_functions: dict[str,
                                     dict[str, Function]] = defaultdict(dict)
        """Dictionary of function's group name and (Dictionary of function name and a Function object)"""
        self.private_function_count: dict[str, int] = defaultdict(int)
        """Current count of how many private functions there are in each group name"""
        self.__scoreboards: dict[str, str] = {
            self.var_name: "dummy"
        }
        """Minecraft scoreboards that are going to be created"""

        self.loads: list[str] = []
        """Output list of commands for load"""
        self.ticks: list[str] = []
        """Output list of commands for tick"""
        self.namespace = namespace
        """Datapack's namespace"""

        self.used_command: set[str] = set()
        """Used JMC command that's for one time call only"""

        self.lexer = lexer
        """Lexer object"""

        self.data = Data()
        """Extra information that can be shared across all JMC function"""

        self.defined_file_pos: dict[str, tuple[Token, Tokenizer]] = {}
        """Dictionary of mcfunction or json path and it's first defined token and tokenizer"""

    def add_objective(self, objective: str, criteria: str = "dummy") -> None:
        """
        Add minecraft scoreboard objective

        :param objective: Name of scoreboard
        :param criteria: Criteria of scoreboard, defaults to 'dummy'
        :raises ValueError: If scoreboard already exists
        """
        if objective in self.__scoreboards and self.__scoreboards[objective] != criteria:
            raise ValueError(
                f"Conflict on adding scoreboard, '{objective}' objective with '{self.__scoreboards[objective]}' criteria already exist.\nGot same objective with '{criteria}' criteria.")
        self.__scoreboards[objective] = criteria

    def get_count(self, name: str) -> str:
        """
        Get count as a string from private function's group

        :param name: Name of the function group
        :return: Count as a string
        """
        count = self.private_function_count[name]
        self.private_function_count[name] += 1
        return str(count)

    def call_func(self, name: str, count: str) -> str:
        """
        Get command string for calling minecraft private function

        :param name: Name of the private function group
        :param count: Name of the function (usually as count)
        :return: String for calling minecraft function
        """
        return f"function {self.namespace}:{self.private_name}/{name}/{count}"

    def add_private_json(self, json_type: str, name: str,
                         json: dict[str, Any] | list[Any]) -> None:
        """
        Add new private json to datapack

        :param json_type: Minecraft json type, for example: tags/functions
        :param name: Name of the private json
        :param json: Dictionary object
        """
        self.jsons[f"{json_type}/{self.private_name}/{name}"] = json

    def add_json(self, json_type: str, name: str,
                 json: dict[str, Any] | list[Any]) -> None:
        """
        Add new private json to datapack

        :param json_type: Minecraft json type, for example: tags/functions
        :param name: Name of the json
        :param json: Dictionary object
        """
        self.jsons[f"{json_type}/{name}"] = json

    def add_arrow_function(self, name: str, token: Token,
                           tokenizer: Tokenizer, force_create_func: bool = False) -> str:
        """
        Add private function for user (arrow function)

        :param name: Private function's group name
        :param token: paren_curly token
        :param tokenizer: token's tokenizer
        :raises JMCSyntaxWarning: If the string in curly bracket is empty
        :return: Minecraft function call string
        """
        if token.string == "{}":
            raise JMCSyntaxWarning("Empty function", token, tokenizer)

        commands = self.parse_function_token(token, tokenizer)
        if not force_create_func and len(
                commands) == 1 and NEW_LINE not in commands[0]:
            return commands[0]

        count = self.get_count(name)
        self.private_functions[name][count] = Function(commands)
        return self.call_func(name, count)

    def add_custom_private_function(self, name: str, token: Token, tokenizer: Tokenizer, count: str,
                                    precommands: list[str] | None = None, postcommands: list[str] | None = None) -> str:
        """
        Wrap custom commands around user's commands

        :param name: Private function's group name
        :param token: paren_curly token
        :param tokenizer: token's tokenizer
        :param count: Name of the function (usually as count)
        :param precommands: Commands before user's commands
        :param postcommands: Commands after user's commands
        :return: Minecraft function call string
        """
        if precommands is None:
            precommands = []
        if postcommands is None:
            postcommands = []

        commands = [*precommands,
                    *self.parse_function_token(token, tokenizer),
                    *postcommands]
        self.private_functions[name][count] = Function(commands)
        return self.call_func(name, count)

    def add_private_function(self, name: str, command: str,
                             count: str | None = None) -> str:
        """
        Add private function but don't create new function unless it's neccessary

        :param name: Name of the private function's group
        :param command: Multiline minecraft command
        :param count: Name of the function (usually as count), defaults to current count + 1
        :return: Minecraft function call string / The command itself
        """

        if "\n" not in command:
            return command

        if count is None:
            count = self.get_count(name)
        self.private_functions[name][count] = Function([command])
        return self.call_func(name, count)

    def add_raw_private_function(
            self, name: str, commands: list[str], count: str | None = None) -> str:
        """
        Add private function for JMC as is

        :param name: Name of the private function's group
        :param commands: List of commands(string)
        :param count: Name of the function (usually as count), defaults to current count + 1
        :return: Minecraft function call string
        """
        if count is None:
            count = self.get_count(name)
        self.private_functions[name][count] = Function(commands)
        return self.call_func(name, count)

    def parse_function_token(self, token: Token,
                             tokenizer: Tokenizer) -> list[str]:
        """
        "Parse a paren_curly token into a list of commands(string)

        :param token: paren_curly token
        :param tokenizer: token's tokenizer
        :return: List of minecraft commands(string)
        """
        return self.lexer.parse_func_content(
            token.string[1:-1], tokenizer.file_path, token.line, token.col, tokenizer.file_string)

    def add_tick_command(self, command: str) -> None:
        """
        Add command to self.ticks

        :param command: Minecraft command string
        """
        self.ticks.append(command)

    def add_load_command(self, command: str) -> None:
        """
        Add command to self.loads

        :param command: Minecraft command string
        """
        self.loads.append(command)

    def add_int(self, integer: int) -> None:
        """
        Add command to self.ints

        :param command: Minecraft command string
        """
        self.ints.add(integer)

    def build(self) -> None:
        """
        Finializing DataPack for building (NO file writing)
        """
        logger.debug("Finializing DataPack")
        if self.ints:
            self.add_objective(self.int_name)
        self.loads[0:0] = [
            *[f"scoreboard objectives add {objective} {criteria}" for objective,
                criteria in self.__scoreboards.items()],
            *[f"scoreboard players set {n} {self.int_name} {n}" for n in self.ints],
        ]
        if self.loads:
            self.functions[self.load_name].insert_extend(self.loads, 0)
        if self.ticks:
            if self.tick_name in self.functions:
                self.functions[self.tick_name].insert_extend(self.ticks, 0)
            else:
                self.functions[self.tick_name] = Function(self.ticks)
        for name, functions in self.private_functions.items():
            for path, func in functions.items():
                self.functions[f"{self.private_name}/{name}/{path}"] = func

        self.private_functions = {}
        self.loads = []
        self.ticks = []

    def parse_func_map(self, token: Token,
                       tokenizer: Tokenizer) -> dict[int, tuple[str, bool]]:
        """
        Parse JMC function hashmap

        :param token: paren_curly token
        :param tokenizer: token's tokenizer
        :param datapack: Datapack object
        :return: Dictionary of integer key and (tuple of function string and whether it is an arrow function)
        """
        func_map: dict[int, tuple[str, bool]] = {}
        for key, value in tokenizer.parse_js_obj(token).items():
            try:
                num = int(key)
            except ValueError as error:
                raise JMCValueError(
                    f"Expected number as key (got {key})", token, tokenizer) from error

            if value.token_type == TokenType.KEYWORD:
                func_map[num] = value.string, False
            elif value.token_type == TokenType.FUNC:
                func_map[num] = "\n".join(
                    self.parse_function_token(value, tokenizer)), True
            else:
                raise JMCValueError(
                    f"Expected function, got {value.token_type.value}", token, tokenizer)
        return func_map

    def parse_list(self, token: Token,
                   tokenizer: Tokenizer, list_of: TokenType) -> list[str]:
        """
        Parse paren_square token into list of strings

        :param token: paren_square token
        :param tokenizer: token's Tokenizer
        :param list_of: TokenType of elements in the list for verification
        :raises JMCValueError: Wrong TokenType
        :return: List of strings
        """
        token_list = tokenizer.parse_list(token)
        for token_ in token_list:
            if token_.token_type != list_of:
                token_type = token_.token_type.value
                if token_.token_type == TokenType.PAREN_SQUARE:
                    token_type = "list"
                raise JMCValueError(
                    f"Expected list/array of {list_of.value}, got list/array of {token_type}", token, tokenizer)
        return [token_.string for token_ in token_list]

    def token_dict_to_raw_js_object(
            self, token_dict: dict[str, Token], tokenizer: Tokenizer) -> str:
        """
        Turns a dictionary of key and token to a string in form of Object

        :param token_dict: Dictionary of string and Token
        :return: String that looks like object
        """
        pairs = []
        for key, token in token_dict.items():
            if token.token_type == TokenType.STRING:
                pairs.append(f"{key}:{token.add_quotation()}")
            elif token.token_type in {TokenType.PAREN_CURLY, TokenType.PAREN_ROUND, TokenType.PAREN_SQUARE}:
                pairs.append(
                    f"{key}:{self.lexer.clean_up_paren_token(token, tokenizer, is_nbt=False)}")
            else:
                pairs.append(f"{key}:{token.string}")
        return "{" + ",".join(pairs) + "}"

    def __repr__(self) -> str:
        return f"""DataPack(
    PRIVATE_NAME = {self.private_name},
    LOAD_NAME = {self.load_name},
    TICK_NAME = {self.tick_name},
    VAR_NAME = {self.var_name},
    INT_NAME = {self.int_name}

    objectives = {dumps(self.__scoreboards, indent=2)}
    ints = {self.ints!r}
    functions = {dumps(self.functions, indent=2, cls=FunctionEncoder)}
    jsons = {dumps(self.jsons, indent=2)}
    private_functions = {dumps(self.private_functions, indent=2, cls=FunctionEncoder)}
    loads = {dumps(self.loads, indent=2)}
    tick = {dumps(self.ticks, indent=2)}
)"""
