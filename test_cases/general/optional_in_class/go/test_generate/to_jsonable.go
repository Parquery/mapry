package somegraph

// File automatically generated by mapry. DO NOT EDIT OR APPEND!

import "fmt"

// WithOptionalToJSONable converts the instance to
// a JSONable representation.
//
// WithOptionalToJSONable requires:
//  * instance != nil
//
// WithOptionalToJSONable ensures:
//  * target != nil
func WithOptionalToJSONable(
	instance *WithOptional) (
	target map[string]interface{}) {

	if instance == nil {
		panic("unexpected nil instance")
	}

	target = make(map[string]interface{})

	////
	// Serialize SomeText
	////

	if instance.SomeText != nil {
		target["some_text"] = (*instance.SomeText)
	}

	return
}

// SomeGraph converts the instance to a JSONable representation.
//
// SomeGraph requires:
//  * instance != nil
//
// SomeGraph ensures:
//  * (err == nil && target != nil) || (err != nil && target == nil)
func SomeGraphToJSONable(
	instance *SomeGraph) (
	target map[string]interface{}, err error) {

	if instance == nil {
		panic("unexpected nil instance")
	}

	target = make(map[string]interface{})
	defer func() {
		if err != nil {
			target = nil
		}
	}()
	////
	// Serialize instance registry of WithOptional
	////

	if len(instance.WithOptionals) > 0 {
		targetWithOptionals := make(map[string]interface{})
		for id := range instance.WithOptionals {
			withOptionalInstance := instance.WithOptionals[id]

			if id != withOptionalInstance.ID {
				err = fmt.Errorf(
					"expected the instance of WithOptional to have the ID %s according to the registry, but got: %s",
					id, withOptionalInstance.ID)
				return
			}

			targetWithOptionals[id] = WithOptionalToJSONable(
				withOptionalInstance)
		}

		target["with_optionals"] = targetWithOptionals
	}

	return
}

// File automatically generated by mapry. DO NOT EDIT OR APPEND!
