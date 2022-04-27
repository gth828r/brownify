class BrownifyError(Exception):
    """Generic error for brownify"""


class DownloadError(BrownifyError):
    """Error raised when unable to download an audio stream

    DownloadError is raised when a downloader fails to fetch audio desired by
    the caller.
    """


class InvalidInputError(BrownifyError):
    """Error raised when invalid user input provided to brownify"""


class MergingError(BrownifyError):
    """Error raised when an error occurs during audio merging

    MergingError should be raised when an error occurs while merging multiple
    separate tracks into a final track.
    """


class NoAudioStreamFoundError(BrownifyError):
    """Error raised when a referenced audio stream does not exist

    NoAudioStreamFoundError should be raised when an audio stream referenced
    by a caller does not exist.
    """


class UnexpectedTokenTypeError(BrownifyError):
    """Error raised when an unexpected token is seen after parsing

    UnexpectedTokenTypeError should be raised when performing post-processing
    steps over input which has already been processed by the grammar. It is
    used to catch issues where the syntax defined by the configuration
    language allows for a class of token which is not semantically understood
    by the program. In general, this should not happen unless there is a bug
    caused by a mismatch between the grammar and the current code logic.
    """


class TokenNotInGrammarError(BrownifyError):
    """Error raised when an token is invalid but passed the parser

    TokenNotInGrammarError should be raised when performing post-processing
    steps over input which has already been processed by the grammar. It is
    used to catch issues where the expected syntax of a token in
    post-processing code does not match the expected syntax of the grammar.
    In general, this should not happen unless there is a bug caused by a
    mismatch between the grammar and the current code logic.
    """


class SplittingError(BrownifyError):
    """Error raised when unable to split a track into multiple tracks

    SplitterError is raised when an error is detected during the splitting
    process.
    """


class NoPipelineSourceError(BrownifyError):
    """Error raised when a pipeline has a source which does not exist

    NoPipelineSourceError should be raised when a pipeline has been defined
    using a source name that has no backing track available.
    """
