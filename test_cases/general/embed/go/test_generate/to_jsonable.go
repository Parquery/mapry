package somegraph

// File automatically generated by mapry. DO NOT EDIT OR APPEND!

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

// NonEmptyToJSONable converts the instance to
// a JSONable representation.
//
// NonEmptyToJSONable requires:
//  * instance != nil
//
// NonEmptyToJSONable ensures:
//  * target != nil
func NonEmptyToJSONable(
	instance *NonEmpty) (
	target map[string]interface{}) {

	if instance == nil {
		panic("unexpected nil instance")
	}

	target = make(map[string]interface{})

	////
	// Serialize Empty
	////

	target["empty"] = EmptyToJSONable(
		&instance.Empty)

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
	// Serialize SomeEmbed
	////

	target["some_embed"] = NonEmptyToJSONable(
		&instance.SomeEmbed)

	return
}

// File automatically generated by mapry. DO NOT EDIT OR APPEND!
