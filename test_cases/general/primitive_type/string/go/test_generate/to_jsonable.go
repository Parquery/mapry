package somegraph

// File automatically generated by mapry. DO NOT EDIT OR APPEND!

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
	// Serialize SomeStr
	////

	target["some_str"] = instance.SomeStr

	////
	// Serialize UnconstrainedStr
	////

	target["unconstrained_str"] = instance.UnconstrainedStr

	return
}

// File automatically generated by mapry. DO NOT EDIT OR APPEND!
