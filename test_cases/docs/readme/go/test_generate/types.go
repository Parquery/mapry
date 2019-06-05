package address

// File automatically generated by mapry. DO NOT EDIT OR APPEND!

import "time"

// Address defines an address.
type Address struct {
	// gives the full address.
	Text string

	// specifies the time zone of the address.
	TimeZone *time.Location
}

// Person defines a contactable person.
type Person struct {
	// identifies the instance
	ID string

	// gives the full name (including middle names).
	FullName string

	// notes where the person lives.
	Address Address

	// points to the image on the disk.
	Picture *string

	// gives the birthday of the person in UTC.
	Birthday time.Time

	// indicates the last modification timestamp.
	LastModified time.Time

	// gives a minimum period between two calls.
	ContactPeriod time.Duration

	// lists friends of the person by nicknames.
	Friends map[string]*Person

	// fires if the user is actively participating.
	Active bool

	// gives height in centimeters.
	Height int64

	// specifies the memebership fee in dollars.
	Fee float64
}

// Pipeline defines an address book.
type Pipeline struct {
	// registers instances of Person.
	Persons map[string]*Person

	// indicates the maintainer of the address book.
	Maintainer *Person
}

// File automatically generated by mapry. DO NOT EDIT OR APPEND!