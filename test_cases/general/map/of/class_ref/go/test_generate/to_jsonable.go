package somegraph

// File automatically generated by mapry. DO NOT EDIT OR APPEND!

import "fmt"

// EmptyToJSONable converts the instance to
// a JSONable representation.
//
// EmptyToJSONable requires:
//  * instance != nil
//
// EmptyToJSONable ensures:
//  * target != nil
func EmptyToJSONable(
	instance *Empty) (
	target map[string]interface{}) {

	if instance == nil {
		panic("unexpected nil instance")
	}

	target = make(map[string]interface{})

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
	// Serialize MapOfClassRefs
	////

	target0 := make(map[string]interface{})
	map0 := instance.MapOfClassRefs
	for k0, v0 := range map0 {
		target0[k0] = v0.ID
	}
	target["map_of_class_refs"] = target0

	////
	// Serialize instance registry of Empty
	////

	if len(instance.Empties) > 0 {
		targetEmpties := make(map[string]interface{})
		for id := range instance.Empties {
			emptyInstance := instance.Empties[id]

			if id != emptyInstance.ID {
				err = fmt.Errorf(
					"expected the instance of Empty to have the ID %s according to the registry, but got: %s",
					id, emptyInstance.ID)
				return
			}

			targetEmpties[id] = EmptyToJSONable(
				emptyInstance)
		}

		target["empties"] = targetEmpties
	}

	return
}

// File automatically generated by mapry. DO NOT EDIT OR APPEND!
