package somegraph

// File automatically generated by mapry. DO NOT EDIT OR APPEND!

import (
	"fmt"
	"regexp"
	"strings"
)

var pattern0 = regexp.MustCompile(
	`^[a-zA-Z]*$`)

// SomeGraphFromJSONable parses SomeGraph from a JSONable value.
//
// If there are any errors, the state of target is undefined.
//
// SomeGraphFromJSONable requires:
//  * target != nil
//  * errors != nil
//  * errors.Empty()
func SomeGraphFromJSONable(
	value interface{},
	ref string,
	target *SomeGraph,
	errors *Errors) {

	if target == nil {
		panic("unexpected nil target")
	}

	if errors == nil {
		panic("unexpected nil errors")
	}

	if !errors.Empty() {
		panic("unexpected non-empty errors")
	}

	cast, ok := value.(map[string]interface{})
	if !ok {
		errors.Add(
			ref,
			fmt.Sprintf(
				"expected a map[string]interface{}, but got: %T",
				value))
		return
	}

	////
	// Parse SomeStr
	////

	value0, ok0 := cast[
		"some_str"]

	if !ok0 {
		errors.Add(
			ref,
			"property is missing: some_str")
	} else {
		cast1, ok1 := value0.(string)
		if !ok1 {
			errors.Add(
				strings.Join(
					[]string{
						ref, "some_str"},
					"/"),
				fmt.Sprintf(
					"expected a string, but got: %T",
					value0))
		} else {
			if !pattern0.MatchString(cast1) {
				errors.Add(
					strings.Join(
						[]string{
							ref, "some_str"},
						"/"),
					fmt.Sprintf(
						"expected to match ^[a-zA-Z]*$, but got: %s",
						cast1))
			} else {
				target.SomeStr = cast1
			}
		}
	}

	if errors.Full() {
		return
	}

	////
	// Parse UnconstrainedStr
	////

	value2, ok2 := cast[
		"unconstrained_str"]

	if !ok2 {
		errors.Add(
			ref,
			"property is missing: unconstrained_str")
	} else {
		cast3, ok3 := value2.(string)
		if !ok3 {
			errors.Add(
				strings.Join(
					[]string{
						ref, "unconstrained_str"},
					"/"),
				fmt.Sprintf(
					"expected a string, but got: %T",
					value2))
		} else {
			target.UnconstrainedStr = cast3
		}
	}

	if errors.Full() {
		return
	}

	return
}

// File automatically generated by mapry. DO NOT EDIT OR APPEND!
