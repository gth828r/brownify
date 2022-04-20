import pyparsing as pp
import pytest

from brownify.errors import UnexpectedTokenTypeError
from brownify.parsers import ActionParser


@pytest.fixture
def dummy_program():
    program = """
    vocals -> save(vocals);
    piano -> save(piano);
    piano -> flat -> save(piano2);
    piano2 -> octaveup -> save(piano3);
    """
    return program


@pytest.fixture
def dummy_program_whitespace():
    program = """
    vocals -> save(vocals);

    piano -> save(piano);

    piano -> flat -> save(piano2);

    piano2 -> octaveup -> save(piano3);
    """
    return program


@pytest.fixture
def dummy_program_num_pipelines():
    return 4


@pytest.fixture
def missing_semicolon_program():
    program = """
    piano -> flat -> save(piano2)
    piano2 -> octaveup -> save(piano3)
    """
    return program


@pytest.fixture
def missing_source_program():
    program = """
    save(vocals);
    """
    return program


@pytest.fixture
def missing_sink_program():
    program = """
    vocals -> flat;
    """
    return program


@pytest.fixture
def invalid_action_program():
    program = """
    vocals -> fake -> save(vocals);
    """
    return program


def test_get_pipelines(dummy_program, dummy_program_num_pipelines):
    parser = ActionParser()
    pipelines = parser.get_pipelines(dummy_program)

    # Check that number of pipelines is correct
    assert len(pipelines) == dummy_program_num_pipelines

    # Check that pipeline internals match expectations
    # piano -> flat -> save(piano2);
    sample_pipeline = pipelines[0]
    assert sample_pipeline.source == "vocals"
    assert sample_pipeline.sink == "vocals"
    assert sample_pipeline.save


def test_get_pipelines_whitespace(
    dummy_program_whitespace, dummy_program_num_pipelines
):
    parser = ActionParser()
    pipelines = parser.get_pipelines(dummy_program_whitespace)

    # Check that number of pipelines is correct
    assert len(pipelines) == dummy_program_num_pipelines

    # Check that pipeline internals match expectations
    # piano -> flat -> save(piano2);
    sample_pipeline = pipelines[0]
    assert sample_pipeline.source == "vocals"
    assert sample_pipeline.sink == "vocals"
    assert sample_pipeline.save


def test_get_pipelines_missing_semicolon(missing_semicolon_program):
    parser = ActionParser()
    with pytest.raises(pp.ParseException):
        parser.get_pipelines(missing_semicolon_program)


def test_get_pipelines_missing_source(missing_source_program):
    parser = ActionParser()
    with pytest.raises(pp.ParseException):
        parser.get_pipelines(missing_source_program)


def test_get_pipelines_missing_sink(missing_sink_program):
    parser = ActionParser()
    with pytest.raises(UnexpectedTokenTypeError):
        parser.get_pipelines(missing_sink_program)


def test_get_pipelines_invalid_action(invalid_action_program):
    parser = ActionParser()
    with pytest.raises(pp.ParseException):
        parser.get_pipelines(invalid_action_program)
