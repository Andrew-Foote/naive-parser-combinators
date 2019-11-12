import typing as t

__version__ = "0.1.0"

# A parser is a function that takes as its argument a sequence of input tokens together with a
# index within that sequence where the parsing should begin, and returns a set containing one
# element for each possible parse, where each element is an output value together with the index
# where the parsing ended.
TokenT = t.TypeVar("TokenT")
ValueT = t.TypeVar("ValueT")
Parser = t.Callable[[t.Sequence[TokenT], int], t.FrozenSet[t.Tuple[ValueT, int]]]


def fail(tokens: t.Sequence, index: int) -> t.FrozenSet:
    """The parser that simply fails, i.e. has no way to parse the input."""
    return frozenset()


def noop(tokens: t.Sequence, index: int) -> t.FrozenSet[t.Tuple[None, int]]:
    """The parser that doesn't consume any tokens and simply outputs `None`."""
    return frozenset({(None, index)})


def consume(pred: t.Callable[[TokenT], bool]) -> Parser[TokenT, TokenT]:
    """A parser that looks at the first token it encounters, calls `pred` on the token and checks
	whether the result is `True`. If so, it consumes and outputs the token. Otherwise, it fails.
	"""
    return lambda tokens, index: (
        frozenset({(tokens[index], index + 1)})
        if index < len(tokens) and pred(tokens[index])
        else frozenset()
    )


ValueT1 = t.TypeVar("ValueT1")
ValueT2 = t.TypeVar("ValueT2")


def compose(
    parser1: Parser[TokenT, ValueT1], parser2: Parser[TokenT, ValueT2]
) -> Parser[TokenT, t.Tuple[ValueT1, ValueT2]]:
    """A parser that delegates to `parser1` and `parser2`, in that order, beginning `parser2` at
	the index where `parser1` ended. If successful, it outputs a 2-tuple containing the output
	from `parser1` and the output from `parser2`, in that order."""
    return lambda tokens, index: (
        frozenset().union(
            *(
                frozenset(
                    {
                        ((value1, value2), index2)
                        for value2, index2 in parser2(tokens, index1)
                    }
                )
                for value1, index1 in parser1(tokens, index)
            )
        )
    )


def either(
    parser1: Parser[TokenT, ValueT1], parser2: Parser[TokenT, ValueT2]
) -> Parser[TokenT, t.Union[ValueT1, ValueT2]]:
    """A parser that can parse the input in either the same way as `parser1` or the same way as
	`parser2`."""
    return lambda tokens, index: parser1(tokens, index) | parser2(tokens, index)


def apply(func: t.Callable[[ValueT1], ValueT2], parser: Parser[TokenT, ValueT1]):
    """A parser that delegates to `parser`, but applies `func` to the output."""
    return lambda tokens, index: frozenset(
        {(func(value), index) for value, index in parser(tokens, index)}
    )


# These are the fundamental parsers; the remaining parsers are built up from these.


def emit(value: ValueT):
    """A parser that doesn't consume any tokens and simply outputs `value`."""
    return apply(lambda _: value, noop)


def transform(
    pred: t.Callable[[TokenT], bool], func: t.Callable[[TokenT], ValueT]
) -> Parser[TokenT, ValueT]:
    """A parser that looks at the first token it encounters, calls `pred` on the token and checks
	whether the result is `True`. If so, it consumes the token, calls `func` on the token and
	outputs the result. Otherwise, it fails."""
    return apply(lambda token: func(token), consume(pred))


ValueT3 = t.TypeVar("ValueT3")


def combine(
    parser1: Parser[TokenT, ValueT1],
    parser2: Parser[TokenT, ValueT2],
    func: t.Callable[[ValueT1, ValueT2], ValueT3],
) -> Parser[TokenT, ValueT3]:
    """A parser that delegates to `parser1` and `parser2`, in that order, beginning `parser2` at
	the index where `parser1` ended. If successful, it calls `func` with the output from `parser`
	as the first argument and the output from `parser2` as the second argument and outputs the
	result."""
    return apply(lambda _: func(_[0], _[1]), compose(parser1, parser2))
