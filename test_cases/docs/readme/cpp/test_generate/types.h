#pragma once

// File automatically generated by mapry. DO NOT EDIT OR APPEND!

#include <boost/filesystem/path.hpp>
#include <optional.hpp>

#include <chrono>
#include <cstdint>
#include <ctime>
#include <map>
#include <memory>
#include <string>

namespace book {
namespace address {

struct Pipeline;

class Person;

struct Address;

// defines an address.
struct Address {
  // gives the full address.
  std::string text;

  // specifies the time zone of the address.
  std::string time_zone;
};

// defines a contactable person.
class Person {
public:
  // identifies the instance.
  std::string id;

  // gives the full name (including middle names).
  std::string full_name;

  // notes where the person lives.
  Address address;

  // points to the image on the disk.
  std::experimental::optional<boost::filesystem::path> picture;

  // gives the birthday of the person in UTC.
  struct tm birthday = tm{0};

  // indicates the last modification timestamp.
  struct tm last_modified = tm{0};

  // gives a minimum period between two calls.
  std::chrono::nanoseconds contact_period;

  // lists friends of the person by nicknames.
  std::map<std::string, Person*> friends;

  // fires if the user is actively participating.
  bool active = false;

  // gives height in centimeters.
  int64_t height = 0;

  // specifies the memebership fee in dollars.
  double fee = 0.0;
};

// defines an address book.
struct Pipeline {
  // indicates the maintainer of the address book.
  Person* maintainer = nullptr;

  // registers Person instances.
  std::map<std::string, std::unique_ptr<Person>> persons;
};

}  // namespace address
}  // namespace book

// File automatically generated by mapry. DO NOT EDIT OR APPEND!