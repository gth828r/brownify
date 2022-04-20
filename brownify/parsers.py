from typing import List, Union

import pyparsing as pp

from brownify.actions import Brownifier
from brownify.errors import TokenNotInGrammarError, UnexpectedTokenTypeError
from brownify.models import Pipeline


class ActionParser:
    """ActionParser defines and parses the recipe grammar

    ActionParser takes in the user provided recipe for the final audio file
    and converts it into a series of Pipelines for processing. It contains
    the grammar definition and also semantic-level processing for the
    conversion of the recipe into Pipelines.
    """

    def __init__(self):
        self._channel = (
            pp.Keyword("bass")
            | pp.Keyword("drums")
            | pp.Keyword("piano")
            | pp.Keyword("other")
            | pp.Keyword("vocals")
        )
        self._entity = pp.Word(pp.alphanums)
        self._source = self._channel | self._entity
        self._drop = pp.Keyword("drop")
        self._var = self._entity
        self._save = pp.Group(
            pp.Literal("save(") + self._entity + pp.Literal(")")
        )
        self._sink = self._drop | self._save | self._var
        self._action = (
            pp.Keyword("early")
            | pp.Keyword("flat")
            | pp.Keyword("halfflat")
            | pp.Keyword("halfsharp")
            | pp.Keyword("late")
            | pp.Keyword("octavedown")
            | pp.Keyword("octaveup")
            | pp.Keyword("sharp")
        )
        self._connector = pp.Literal("->")
        self._expression = pp.Group(
            self._source
            + self._connector
            + (self._action + self._connector)[0, ...]
            + self._sink
        )
        self._eol = pp.Literal(";")
        self._pipelines = (
            self._expression
            + (self._eol + self._expression)[0, ...]
            + self._eol[0, 1]
        )

        self._fn_map = {
            "early": Brownifier.early,
            "flat": Brownifier.flat,
            "halfflat": Brownifier.half_flat,
            "halfsharp": Brownifier.half_sharp,
            "late": Brownifier.late,
            "octavedown": Brownifier.octave_down,
            "octaveup": Brownifier.octave_up,
            "sharp": Brownifier.sharp,
        }

    @staticmethod
    def _matches_parser_element(token: str, pe: pp.ParserElement) -> bool:
        # FIXME: Is there a better way?
        try:
            pe.parseString(token)
            return True
        except pp.ParseException:
            return False

    def _is_action(self, token: str) -> bool:
        return self._matches_parser_element(token, self._action)

    def _is_connector(self, token: str) -> bool:
        return self._matches_parser_element(token, self._connector)

    def _is_source(self, token: str) -> bool:
        return self._matches_parser_element(token, self._source)

    def _is_sink(self, token: str) -> bool:
        return self._matches_parser_element(token, self._sink)

    def _is_save(self, token: str) -> bool:
        return self._matches_parser_element(token, self._save)

    def _is_drop(self, token: str) -> bool:
        return self._matches_parser_element(token, self._drop)

    @staticmethod
    def _split_into_expressions(
        program: pp.ParseResults,
    ) -> List[List[Union[str, List[str]]]]:
        pipeline_specs = []
        for expression in program.asList():
            if expression != ";":
                pipeline_specs.append(expression)

        return pipeline_specs

    def _convert_into_pipeline(
        self, expression: List[Union[str, List[str]]]
    ) -> Union[Pipeline, None]:
        if len(expression) == 0:
            return None

        if not isinstance(expression[0], str) or not self._is_source(
            expression[0]
        ):
            raise UnexpectedTokenTypeError(
                "The first element of an expression in a recipe must be a "
                f"valid source, but got {expression[0]}."
            )

        source: str = expression[0]
        actions = []
        sink: Union[str, None] = None
        save = False
        for item in expression[1:]:
            # We need to handle both individual tokens and grouped tokens.
            # An example of a grouped token is a save token, which will
            # take the form ["save(", "NAME", ")"].
            token = None
            if isinstance(item, str):
                token = item
            elif isinstance(item, list):
                token = "".join(item)
            else:
                raise UnexpectedTokenTypeError(
                    f"Encountered unexpected token type: {type(token)}"
                )

            # Parse the input program to construct pipelines
            if self._is_action(token):
                actions.append(self._fn_map[item])
            elif self._is_sink(token):
                if self._is_drop(token):
                    return None
                elif self._is_save(token):
                    # Skip over the part of the lit that says "save(" and ")"
                    # There should only be one element.
                    sink_name_parts = item[1:-1]
                    if len(sink_name_parts) != 1:
                        raise TokenNotInGrammarError(
                            f"Token {token} is not a valid save declaration"
                        )

                    sink = sink_name_parts[0]
                    save = True
                else:
                    sink = token
            elif self._is_connector(token):
                continue
            else:
                raise TokenNotInGrammarError(
                    f"Token {token} is not part of valid grammar"
                )

        if not isinstance(sink, str):
            raise UnexpectedTokenTypeError(
                f"No valid sink was provided in expression:\n{expression}"
            )

        return Pipeline(source=source, actions=actions, sink=sink, save=save)

    def get_pipelines(self, program: str) -> List[Pipeline]:
        """Get audio processing pipelines given a recipe

        Args:
            program: Recipe defining the steps to perform over the audio

        Returns:
            Sequence of pipelines to be run
        """
        parsed = self._pipelines.parseString(program, parseAll=True)
        pipeline_exprs = self._split_into_expressions(parsed)

        pipelines = []
        for pipeline_expr in pipeline_exprs:
            pipeline = self._convert_into_pipeline(pipeline_expr)
            if pipeline:
                pipelines.append(pipeline)

        return pipelines
