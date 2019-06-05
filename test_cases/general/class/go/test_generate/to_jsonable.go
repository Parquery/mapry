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

// WithReferenceToJSONable converts the instance to
// a JSONable representation.
//
// WithReferenceToJSONable requires:
//  * instance != nil
//
// WithReferenceToJSONable ensures:
//  * target != nil
func WithReferenceToJSONable(
	instance *WithReference) (
	target map[string]interface{}) {

	if instance == nil {
		panic("unexpected nil instance")
	}

	target = make(map[string]interface{})

	////
	// Serialize ReferenceToAnEmpty
	////

	target["reference_to_an_empty"] = instance.ReferenceToAnEmpty.ID

	////
	// Serialize ArrayOfEmpties
	////

	count0 := len(instance.ArrayOfEmpties)
	slice0 := instance.ArrayOfEmpties
	target0 := make([]interface{}, count0)
	for i0 := 0; i0 < count0; i0++ {
		target0[i0] = slice0[i0].ID
	}
	target["array_of_empties"] = target0

	////
	// Serialize MapOfEmpties
	////

	target1 := make(map[string]interface{})
	map1 := instance.MapOfEmpties
	for k1, v1 := range map1 {
		target1[k1] = v1.ID
	}
	target["map_of_empties"] = target1

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
	// Serialize GlobalReferenceToAnEmpty
	////

	target["global_reference_to_an_empty"] = instance.GlobalReferenceToAnEmpty.ID

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

	////
	// Serialize instance registry of WithReference
	////

	if len(instance.WithReferences) > 0 {
		targetWithReferences := make(map[string]interface{})
		for id := range instance.WithReferences {
			withReferenceInstance := instance.WithReferences[id]

			if id != withReferenceInstance.ID {
				err = fmt.Errorf(
					"expected the instance of WithReference to have the ID %s according to the registry, but got: %s",
					id, withReferenceInstance.ID)
				return
			}

			targetWithReferences[id] = WithReferenceToJSONable(
				withReferenceInstance)
		}

		target["with_references"] = targetWithReferences
	}

	return
}

// File automatically generated by mapry. DO NOT EDIT OR APPEND!