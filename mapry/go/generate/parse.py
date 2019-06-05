"""Generate the code that defines general structures required for parsing."""

from icontract import ensure

import mapry
import mapry.go.generate
import mapry.go.jinja2_env
import mapry.indention

_DEFINE_ERROR_AND_ERRORS = '''\
// Error represents a parsing error.
type Error struct {
    // references the cause (e.g., a reference path).
    Ref string

    // describes the error.
    Message string
}

// Errors collects parsing errors capped at a certain quantity.
//
// If the capacity is full, the subsequent surplus errors are ignored.
type Errors struct {
    // lists errors recorded during parsing.
    values []Error

    // indicates the capacity of the error container.
    cap uint64
}

// NewErrors initializes a new error container with the capacity `cap`.
//
// The capacity of 0 means infinite capacity.
func NewErrors(cap uint64) (e *Errors) {
    return &Errors{
        values: make([]Error, 0, cap),
        cap:    cap}
}

// Values gets the contained errors.
//
// The caller should not modify the returned errors.
func (e *Errors) Values() []Error {
    return e.values
}

// Add inserts the error into the container.
//
// ref indicates the cause (e.g., as a reference path).
// message describes the error.
// If the capacity is full, the subsequent surplus errors are ignored.
func (e *Errors) Add(ref string, message string) {
    if e.cap == 0 || uint64(len(e.values)) < e.cap {
        e.values = append(e.values, Error{Ref: ref, Message: message})
    }
}

// Full indicates whether the container is full.
func (e *Errors) Full() bool {
    return e.cap != 0 && uint64(len(e.values)) == e.cap
}

// Empty indicates whether no parsing errors occurred.
func (e *Errors) Empty() bool {
    return uint64(len(e.values)) == 0
}'''


@ensure(lambda result: result.endswith('\n'))
def generate(go: mapry.Go) -> str:
    """
    Generate the souce file to define general structures required for parsing.

    :return: content of the source file
    """
    blocks = [
        "package {}".format(go.package), mapry.go.generate.WARNING,
        _DEFINE_ERROR_AND_ERRORS, mapry.go.generate.WARNING
    ]

    return mapry.indention.reindent(
        text='\n\n'.join(blocks) + '\n', indention='\t')
