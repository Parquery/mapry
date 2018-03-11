// File automatically generated by mapry. DO NOT EDIT OR APPEND!

#include "jsoncpp.h"
#include "parse.h"
#include "types.h"

#include <cmath>
#include <cstring>
#include <iomanip>
#include <limits>
#include <memory>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>

namespace some {
namespace graph {

namespace jsoncpp {

/**
 * generates an error message.
 *
 * @param cc char array as the description part of the message
 * @param cc_size size of the char array
 * @param s string as the detail part of the message
 * @return concatenated string
 */
std::string message(const char* cc, size_t cc_size, std::string s) {
  std::string result;
  result.reserve(cc_size + s.size());
  result.append(cc, cc_size);
  result.append(s);
  return result;
}

namespace re {
const std::regex kDuration(
  "^(\\+|-)?P(((0|[1-9][0-9]*)(\\.[0-9]+)?)Y)?"
  "(((0|[1-9][0-9]*)(\\.[0-9]+)?)M)?"
  "(((0|[1-9][0-9]*)(\\.[0-9]+)?)W)?"
  "(((0|[1-9][0-9]*)(\\.[0-9]+)?)D)?"
  "(T"
  "(((0|[1-9][0-9]*)(\\.[0-9]+)?)H)?"
  "(((0|[1-9][0-9]*)(\\.[0-9]+)?)M)?"
  "(((0|[1-9][0-9]*)(\\.([0-9]+))?)S)?"
  ")?$");
}  // namespace re

/**
 * adds the left and the right and checks for the overflow.
 *
 * left and right are expected to be non-negative.
 *
 * @param[in] left summand
 * @param[in] right summand
 * @param[out] overflows true if the addition overflows
 * @return sum
 */
template <typename rep_t>
rep_t add_rep_double(rep_t left, double right, bool* overflows) {
  if (left < 0) {
    throw std::invalid_argument("Expected left >= 0");
  }

  if (right < 0) {
    throw std::invalid_argument("Expected right >= 0");
  }

  // 9223372036854775808 == 2^63, the first double that is
  // greater than max int64 (max int64 is 2^63 - 1).
  if (right >= 9223372036854775808.0) {
    *overflows = true;
    return 0;
  }

  const rep_t rightRep = right;

  if (rightRep > std::numeric_limits<rep_t>::max() - left) {
    *overflows = true;
    return 0;
  }

  return rightRep + left;
}

/**
 * parses the duration from a string.
 *
 *  Following STL chrono library, the following units are counted as:
 *   - years as 365.2425 days (the average length of a Gregorian year),
 *   - months as 30.436875 days (exactly 1/12 of years) and
 *   - weeks as 7 days.
 *
 * See https://en.cppreference.com/w/cpp/chrono/duration for details.
 *
 * @param[in] s string to parse
 * @param[out] error error message, if any
 * @return parsed duration
 */
std::chrono::nanoseconds duration_from_string(
    const std::string& s,
    std::string* error) {
  std::smatch mtch;
  const bool matched = std::regex_match(s, mtch, re::kDuration);

  if (not matched) {
    std::stringstream sserr;
    sserr << "failed to match the duration: " << s;
    *error = sserr.str();
    return std::chrono::nanoseconds();
  }

  typedef std::chrono::nanoseconds::rep rep_t;

  ////
  // Extract nanoseconds
  ////

  const std::string nanoseconds_str = mtch[31];
  rep_t nanoseconds;
  if (nanoseconds_str.size() == 0) {
    // No nanoseconds specified
    nanoseconds = 0;
  } else if(nanoseconds_str.size() <= 9) {
    size_t first_nonzero = 0;
    for (; first_nonzero < nanoseconds_str.size();
        ++first_nonzero) {
      if (nanoseconds_str[first_nonzero] >= '0' and
          nanoseconds_str[first_nonzero] <= '9') {
        break;
      }
    }

    if (first_nonzero == nanoseconds_str.size()) {
      // No non-zero numbers, all zeros behind the seconds comma
      nanoseconds = 0;
    } else {
      const rep_t fraction_as_integer(
        std::atol(&nanoseconds_str[first_nonzero]));

      const size_t order = 9 - nanoseconds_str.size();
      rep_t multiplier = 1;
      for (size_t i = 0; i < order; ++i) {
        multiplier *= 10;
      }

      nanoseconds = fraction_as_integer * multiplier;
    }
  } else {
    // Signal that the precision is lost
    std::stringstream sserr;
    sserr << "converting the duration to nanoseconds "
      "results in loss of precision: " << s;
    *error = sserr.str();
    return std::chrono::nanoseconds();
  }

  ////
  // Extract all the other interval counts
  ////

  const std::string sign_str = mtch[1];
  const rep_t sign = (sign_str.empty() or sign_str == "+") ? 1 : -1;

  const double years(
    (mtch[3].length() == 0) ? 0.0 : std::stod(mtch[3]));
  const double months(
    (mtch[7].length() == 0) ? 0.0 : std::stod(mtch[7]));
  const double weeks(
    (mtch[11].length() == 0) ? 0.0 : std::stod(mtch[11]));
  const double days(
    (mtch[15].length() == 0) ? 0.0 : std::stod(mtch[15]));
  const double hours(
    (mtch[20].length() == 0) ? 0.0 : std::stod(mtch[20]));
  const double minutes(
    (mtch[24].length() == 0) ? 0.0 : std::stod(mtch[24]));
  const rep_t seconds(
    (mtch[29].length() == 0) ? 0 : std::stol(mtch[29]));

  ////
  // Sum
  ////

  rep_t sum = nanoseconds;

  const rep_t max_seconds(
    std::numeric_limits<rep_t>::max() / (1000L * 1000L * 1000L));
  if (seconds > max_seconds) {
    std::stringstream sserr;
    sserr << "seconds in duration overflow as nanoseconds: " << s;
    *error = sserr.str();
    return std::chrono::nanoseconds();
  }

  const rep_t seconds_as_ns = seconds * 1000L * 1000L * 1000L;
  if (sum > std::numeric_limits<rep_t>::max() - seconds_as_ns) {
    std::stringstream sserr;
    sserr << "duration overflow as nanoseconds: " << s;
    *error = sserr.str();
    return std::chrono::nanoseconds();
  }
  sum += seconds_as_ns;

  bool overflows;

  sum = add_rep_double(
    sum, minutes * 6e10, &overflows);
  if (overflows) {
    std::stringstream sserr;
    sserr << "duration overflows as nanoseconds: " << s;
    *error = sserr.str();
    return std::chrono::nanoseconds();
  }

  sum = add_rep_double(
    sum, hours * 3.6e12, &overflows);
  if (overflows) {
    std::stringstream sserr;
    sserr << "duration overflows as nanoseconds: " << s;
    *error = sserr.str();
    return std::chrono::nanoseconds();
  }

  sum = add_rep_double(
    sum, days * 24.0 * 3.6e12, &overflows);
  if (overflows) {
    std::stringstream sserr;
    sserr << "duration overflows as nanoseconds: " << s;
    *error = sserr.str();
    return std::chrono::nanoseconds();
  }

  sum = add_rep_double(
    sum, weeks * 7.0 * 24.0 * 3.6e12, &overflows);
  if (overflows) {
    std::stringstream sserr;
    sserr << "duration overflows as nanoseconds: " << s;
    *error = sserr.str();
    return std::chrono::nanoseconds();
  }

  sum = add_rep_double(
    sum, months * 30.436875 * 24.0 * 3.6e12, &overflows);
  if (overflows) {
    std::stringstream sserr;
    sserr << "duration overflows as nanoseconds: " << s;
    *error = sserr.str();
    return std::chrono::nanoseconds();
  }

  sum = add_rep_double(
    sum, years * 365.2425 * 24.0 * 3.6e12, &overflows);
  if (overflows) {
    std::stringstream sserr;
    sserr << "duration overflows as nanoseconds: " << s;
    *error = sserr.str();
    return std::chrono::nanoseconds();
  }

  // sum is always positive, so the multiplication by -1 can not
  // overflow since |max rep_t| < |min rep_t|
  if (sign < 0) {
    sum = -sum;
  }

  return std::chrono::nanoseconds(sum);
}

/**
 * converts a JSON value type to a human-readable string representation.
 *
 * @param value_type to be converted
 * @return string representation of the JSON value type
 */
std::string value_type_to_string(Json::ValueType value_type) {
  switch (value_type) {
    case Json::ValueType::nullValue: return "null";
    case Json::ValueType::intValue: return "int";
    case Json::ValueType::uintValue: return "uint";
    case Json::ValueType::realValue: return "real";
    case Json::ValueType::stringValue: return "string";
    case Json::ValueType::booleanValue: return "bool";
    case Json::ValueType::arrayValue: return "array";
    case Json::ValueType::objectValue: return "object";
    default:
      std::stringstream ss;
      ss << "Unhandled value type in value_to_string: "
        << value_type;
      throw std::domain_error(ss.str());
  }
}

void some_graph_from(
    const Json::Value& value,
    std::string ref,
    SomeGraph* target,
    parse::Errors* errors) {
  if (errors == nullptr) {
    throw std::invalid_argument("Unexpected null errors");
  }

  if (not errors->empty()) {
    throw std::invalid_argument("Unexpected non-empty errors");
  }

  if (not value.isObject()) {
    constexpr auto expected_but_got(
      "Expected an object, but got: ");

    errors->add(
      ref,
      message(
        expected_but_got,
        strlen(expected_but_got),
        value_type_to_string(
          value.type())));
    return;
  }

  ////
  // Pre-allocate empties
  ////

  std::string empties_ref;
  empties_ref.reserve(ref.size() + 8);
  empties_ref += ref;
  empties_ref += "/empties";

  if (value.isMember("empties")) {
    const Json::Value& obj = value["empties"];
    if (not obj.isObject()) {
      constexpr auto expected_but_got(
        "Expected an object, but got: ");

      errors->add(
        empties_ref,
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            obj.type())));
    } else {
      for (Json::ValueConstIterator it = obj.begin();
          it != obj.end(); ++it) {
                auto instance = std::make_unique<Empty>();
        instance->id = it.name();
        target->empties[it.name()] = std::move(instance);

      }
    }
  }

  // Pre-allocating class instances is critical.
  // If the pre-allocation failed, we can not continue to parse the instances.
  if (not errors->empty()) {
    return;
  }

  // Keep the prefix fixed in this buffer so that
  // it is copied as little as possible
  std::string instance_ref;

  ////
  // Parse empties
  ////

  // clear() does not shrink the reserved memory,
  // see https://en.cppreference.com/w/cpp/string/basic_string/clear
  instance_ref.clear();
  instance_ref += empties_ref;
  instance_ref += '/';

  if (value.isMember("empties")) {
    const Json::Value& obj = value["empties"];

    for (Json::ValueConstIterator it = obj.begin(); it != obj.end(); ++it) {
      instance_ref.reserve(
        empties_ref.size() + 1 + it.name().size());
      instance_ref.resize(
        empties_ref.size() + 1);
      instance_ref.append(
        it.name());

      Empty* instance(
        target->empties.at(it.name()).get());
      empty_from(
        *it,
        instance_ref,
        instance,
        errors);

      if (errors->full()) {
        break;
      }
    }
  }
  if (errors->full()) {
    return;
  }

  ////
  // Parse optional_array
  ////

  if (value.isMember("optional_array")) {
    target->optional_array.emplace();
    const Json::Value& value_0 = value["optional_array"];
    if (not value_0.isArray()) {
      constexpr auto expected_but_got(
        "Expected an array, but got: ");

      errors->add(
        std::string(ref)
          .append("/optional_array"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_0.type())));
    } else {
      std::vector<int64_t>& target_0 = *target->optional_array;
      target_0.resize(value_0.size());
      size_t i_0 = 0;
      for (const Json::Value& item_0 : value_0) {
        if (not item_0.isInt64()) {
          constexpr auto expected_but_got(
            "Expected an int64, but got: ");

          errors->add(
            std::string(ref)
              .append("/optional_array")
              .append("/")
              .append(std::to_string(i_0)),
            message(
              expected_but_got,
              strlen(expected_but_got),
              value_type_to_string(
                item_0.type())));
        } else {
          target_0.at(i_0) = item_0.asInt64();
        }
        ++i_0;

        if (errors->full()) {
          break;
        }
      }

    }
  }
  if (errors->full()) {
    return;
  }

  ////
  // Parse optional_boolean
  ////

  if (value.isMember("optional_boolean")) {
    const Json::Value& value_2 = value["optional_boolean"];
    if (not value_2.isBool()) {
      constexpr auto expected_but_got(
        "Expected a bool, but got: ");

      errors->add(
        std::string(ref)
          .append("/optional_boolean"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_2.type())));
    } else {
      target->optional_boolean = value_2.asBool();
    }
  }
  if (errors->full()) {
    return;
  }

  ////
  // Parse optional_date
  ////

  if (value.isMember("optional_date")) {
    const Json::Value& value_3 = value["optional_date"];
    if (not value_3.isString()) {
      constexpr auto expected_but_got(
        "Expected a string, but got: ");

      errors->add(
        std::string(ref)
          .append("/optional_date"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_3.type())));
    } else {
      const std::string cast_3 = value_3.asString();
      struct tm tm_3 = tm{0};
      char* ret_3 = strptime(
        cast_3.c_str(),
        "%Y-%m-%d",
        &tm_3);

      if (ret_3 == nullptr or *ret_3 != '\0') {
        constexpr auto expected_but_got(
          "Expected to strptime "
          "%Y-%m-%d"
          ", but got: ");

        errors->add(
          std::string(ref)
            .append("/optional_date"),
          message(
            expected_but_got,
            strlen(expected_but_got),
            cast_3));
      } else {
        target->optional_date = tm_3;
      }
    }
  }
  if (errors->full()) {
    return;
  }

  ////
  // Parse optional_datetime
  ////

  if (value.isMember("optional_datetime")) {
    const Json::Value& value_4 = value["optional_datetime"];
    if (not value_4.isString()) {
      constexpr auto expected_but_got(
        "Expected a string, but got: ");

      errors->add(
        std::string(ref)
          .append("/optional_datetime"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_4.type())));
    } else {
      const std::string cast_4 = value_4.asString();
      struct tm tm_4 = tm{0};
      char* ret_4 = strptime(
        cast_4.c_str(),
        "%Y-%m-%dT%H:%M:%SZ",
        &tm_4);

      if (ret_4 == nullptr or *ret_4 != '\0') {
        constexpr auto expected_but_got(
          "Expected to strptime "
          "%Y-%m-%dT%H:%M:%SZ"
          ", but got: ");

        errors->add(
          std::string(ref)
            .append("/optional_datetime"),
          message(
            expected_but_got,
            strlen(expected_but_got),
            cast_4));
      } else {
        target->optional_datetime = tm_4;
      }
    }
  }
  if (errors->full()) {
    return;
  }

  ////
  // Parse optional_duration
  ////

  if (value.isMember("optional_duration")) {
    const Json::Value& value_5 = value["optional_duration"];
    if (not value_5.isString()) {
      constexpr auto expected_but_got(
        "Expected a string, but got: ");

      errors->add(
        std::string(ref)
          .append("/optional_duration"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_5.type())));
    } else {
      const std::string cast_5_str = value_5.asString();
      std::string error_5;
      std::chrono::nanoseconds cast_5 = duration_from_string(
        cast_5_str, &error_5);

      if (not error_5.empty()) {
        constexpr auto invalid_duration(
          "Invalid duration: ");

        errors->add(
          std::string(ref)
            .append("/optional_duration"),
          message(
            invalid_duration,
            strlen(invalid_duration),
            error_5));
      } else {
        target->optional_duration = cast_5;
      }
    }
  }
  if (errors->full()) {
    return;
  }

  ////
  // Parse optional_float
  ////

  if (value.isMember("optional_float")) {
    const Json::Value& value_6 = value["optional_float"];
    if (not value_6.isDouble()) {
      constexpr auto expected_but_got(
        "Expected a double, but got: ");

      errors->add(
        std::string(ref)
          .append("/optional_float"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_6.type())));
    } else {
      target->optional_float = value_6.asDouble();
    }
  }
  if (errors->full()) {
    return;
  }

  ////
  // Parse optional_integer
  ////

  if (value.isMember("optional_integer")) {
    const Json::Value& value_7 = value["optional_integer"];
    if (not value_7.isInt64()) {
      constexpr auto expected_but_got(
        "Expected an int64, but got: ");

      errors->add(
        std::string(ref)
          .append("/optional_integer"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_7.type())));
    } else {
      target->optional_integer = value_7.asInt64();
    }
  }
  if (errors->full()) {
    return;
  }

  ////
  // Parse optional_map
  ////

  if (value.isMember("optional_map")) {
    target->optional_map.emplace();
    const Json::Value& value_8 = value["optional_map"];
    if (not value_8.isObject()) {
      constexpr auto expected_but_got(
        "Expected an object, but got: ");

      errors->add(
        std::string(ref)
          .append("/optional_map"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_8.type())));
    } else {
      std::map<std::string, int64_t>& target_8 = *target->optional_map;
      for (Json::ValueConstIterator it_8 = value_8.begin(); it_8 != value_8.end(); ++it_8) {
        const Json::Value& value_9 = *it_8;
        if (not value_9.isInt64()) {
          constexpr auto expected_but_got(
            "Expected an int64, but got: ");

          errors->add(
            std::string(ref)
              .append("/optional_map")
              .append("/")
              .append(it_8.name()),
            message(
              expected_but_got,
              strlen(expected_but_got),
              value_type_to_string(
                value_9.type())));
        } else {
          target_8[it_8.name()] = value_9.asInt64();
        }

        if (errors->full()) {
          break;
        }
      }
    }
  }
  if (errors->full()) {
    return;
  }

  ////
  // Parse optional_path
  ////

  if (value.isMember("optional_path")) {
    const Json::Value& value_10 = value["optional_path"];
    if (not value_10.isString()) {
      constexpr auto expected_but_got(
        "Expected a string, but got: ");

      errors->add(
        std::string(ref)
          .append("/optional_path"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_10.type())));
    } else {
        target->optional_path = boost::filesystem::path(
        value_10.asString());

    }
  }
  if (errors->full()) {
    return;
  }

  ////
  // Parse optional_string
  ////

  if (value.isMember("optional_string")) {
    const Json::Value& value_11 = value["optional_string"];
    if (not value_11.isString()) {
      constexpr auto expected_but_got(
        "Expected a string, but got: ");

      errors->add(
        std::string(ref)
          .append("/optional_string"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_11.type())));
    } else {
      target->optional_string = value_11.asString();
    }
  }
  if (errors->full()) {
    return;
  }

  ////
  // Parse optional_time
  ////

  if (value.isMember("optional_time")) {
    const Json::Value& value_12 = value["optional_time"];
    if (not value_12.isString()) {
      constexpr auto expected_but_got(
        "Expected a string, but got: ");

      errors->add(
        std::string(ref)
          .append("/optional_time"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_12.type())));
    } else {
      const std::string cast_12 = value_12.asString();
      struct tm tm_12 = tm{0};
      char* ret_12 = strptime(
        cast_12.c_str(),
        "%H:%M:%S",
        &tm_12);

      if (ret_12 == nullptr or *ret_12 != '\0') {
        constexpr auto expected_but_got(
          "Expected to strptime "
          "%H:%M:%S"
          ", but got: ");

        errors->add(
          std::string(ref)
            .append("/optional_time"),
          message(
            expected_but_got,
            strlen(expected_but_got),
            cast_12));
      } else {
        target->optional_time = tm_12;
      }
    }
  }
  if (errors->full()) {
    return;
  }

  ////
  // Parse optional_time_zone
  ////

  if (value.isMember("optional_time_zone")) {
    const Json::Value& value_13 = value["optional_time_zone"];
    if (not value_13.isString()) {
      constexpr auto expected_but_got(
        "Expected a string, but got: ");

      errors->add(
        std::string(ref)
          .append("/optional_time_zone"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_13.type())));
    } else {
      target->optional_time_zone = value_13.asString();
    }
  }
  if (errors->full()) {
    return;
  }

  ////
  // Parse optional_reference
  ////

  if (value.isMember("optional_reference")) {
    const Json::Value& value_14 = value["optional_reference"];
    if (not value_14.isString()) {
      constexpr auto expected_but_got(
        "Expected a string, but got: ");

      errors->add(
        std::string(ref)
          .append("/optional_reference"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_14.type())));
    } else {
      const std::string& cast_14 = value_14.asString();
      if (target->empties.count(cast_14) == 0) {
        constexpr auto reference_not_found(
          "Reference to an instance of class "
          "Empty"
          " not found: ");

        errors->add(
          std::string(ref)
            .append("/optional_reference"),
          message(
            reference_not_found,
            strlen(reference_not_found),
            cast_14));
      } else {
        target->optional_reference = target->empties.at(cast_14).get();
      }
    }
  }
  if (errors->full()) {
    return;
  }

  ////
  // Parse optional_embed
  ////

  if (value.isMember("optional_embed")) {
    target->optional_embed.emplace();
    const Json::Value& value_15 = value["optional_embed"];
    some_embed_from(
      value_15,
      std::string(ref)
        .append("/optional_embed"),
      &(*target->optional_embed),
      errors);
  }
  if (errors->full()) {
    return;
  }
}

/**
 * serializes the date/time/datetime to a string.
 *
 * @param[in] t time structure
 * @param[in] fmt format
 * @return time structure serialized to a string according to the format
 */
std::string tm_to_string(const struct tm& t, const char* fmt) {{
  if(fmt == nullptr or fmt[0] == '\0') {
    return "";
  }

  const size_t fmt_size = strlen(fmt);

  std::string buf;
  buf.resize(fmt_size * 4);
  int len = strftime(&buf[0], buf.size(), fmt, &t);

  while(len == 0) {{
    buf.resize(buf.size() * 2);
    int len = strftime(&buf[0], buf.size(), fmt, &t);
  }}
  buf.resize(len);
  return buf;
}}

/**
 * serializes the duration to a string.
 *
 * @param[in] d duration to be serialized
 * @return duration as string
 */
std::string duration_to_string(const std::chrono::nanoseconds& d) {
  typedef std::chrono::nanoseconds::rep rep_t;

  const rep_t abscount = (d.count() < 0) ? -d.count() : d.count();
  if (abscount < 0) {
    std::stringstream sserr;
    sserr
      << "Computing the absolute number of nanoseconds "
        "in the duration underflowed: "
      << d.count();
    throw std::overflow_error(sserr.str());
  }

  const rep_t nanoseconds_in_day = 86400L*1000L*1000L*1000L;
  const rep_t days = abscount / nanoseconds_in_day;
  rep_t rest = abscount % nanoseconds_in_day;

  const rep_t nanoseconds_in_hour = 3600L*1000L*1000L*1000L;
  const rep_t hours = rest / nanoseconds_in_hour;
  rest = rest % nanoseconds_in_hour;

  const rep_t nanoseconds_in_minute = 60L*1000L*1000L*1000L;
  const rep_t minutes = rest / nanoseconds_in_minute;
  rest = rest % nanoseconds_in_minute;

  const rep_t nanoseconds_in_second = 1000L*1000L*1000L;
  const rep_t seconds = rest / nanoseconds_in_second;
  rest = rest % nanoseconds_in_second;

  const rep_t nanoseconds = rest;

  std::stringstream ss;
  if (d.count() < 0) {
    ss << "-";
  }

  ss << "P";

  if(days > 0) {
    ss << days << "D";
  }

  if(hours > 0 or minutes > 0 or
      seconds > 0 or nanoseconds > 0) {
    ss << "T";

    if(hours > 0) {
      ss << hours << "H";
    }

    if(minutes > 0) {
      ss << minutes << "M";
    }

    if(nanoseconds == 0) {
      if(seconds > 0) {
        ss << seconds << "S";
      }
    } else {
      std::stringstream ssnano;
      ssnano << std::setfill('0') << std::setw(9) << nanoseconds;
      const std::string nanos_str = ssnano.str();

      // Nag trailing zeros
      size_t i = nanos_str.size() - 1;
      for(; i >= 0; --i) {
        if (nanos_str.at(i) != '0') {
          break;
        }
      }

      ss << seconds << "." << nanos_str.substr(0, i + 1) << "S";
    }
  }

  return ss.str();
}

void empty_from(
    const Json::Value& value,
    std::string ref,
    Empty* target,
    parse::Errors* errors) {
  if (not value.isObject()) {
    constexpr auto expected_but_got(
      "Expected an object, but got: ");

    errors->add(
      ref,
      message(
        expected_but_got,
        strlen(expected_but_got),
        value_type_to_string(
          value.type())));
    return;
  }
}

void some_embed_from(
    const Json::Value& value,
    std::string ref,
    SomeEmbed* target,
    parse::Errors* errors) {
  if (not value.isObject()) {
    constexpr auto expected_but_got(
      "Expected an object, but got: ");

    errors->add(
      ref,
      message(
        expected_but_got,
        strlen(expected_but_got),
        value_type_to_string(
          value.type())));
    return;
  }
}

Json::Value serialize_empty(
    const Empty& empty) {
  return Json::objectValue;
}

Json::Value serialize_some_embed(
    const SomeEmbed& some_embed) {
  return Json::objectValue;
}

Json::Value serialize_some_graph(
    const SomeGraph& some_graph) {
  Json::Value some_graph_as_value;

  if (some_graph.optional_array) {
    Json::Value target_0(Json::arrayValue);
    const auto& vector_0 = (*some_graph.optional_array);
    for (int i_0 = 0;
        i_0 < vector_0.size();
        ++i_0) {
      target_0[i_0] = vector_0[i_0];
    }
    some_graph_as_value["optional_array"] = std::move(target_0);
  }

  if (some_graph.optional_boolean) {
    some_graph_as_value["optional_boolean"] = (*some_graph.optional_boolean);
  }

  if (some_graph.optional_date) {
    some_graph_as_value["optional_date"] = tm_to_string(
      (*some_graph.optional_date),
      "%Y-%m-%d");
  }

  if (some_graph.optional_datetime) {
    some_graph_as_value["optional_datetime"] = tm_to_string(
      (*some_graph.optional_datetime),
      "%Y-%m-%dT%H:%M:%SZ");
  }

  if (some_graph.optional_duration) {
    some_graph_as_value["optional_duration"] = duration_to_string((*some_graph.optional_duration));
  }

  if (some_graph.optional_float) {
    some_graph_as_value["optional_float"] = (*some_graph.optional_float);
  }

  if (some_graph.optional_integer) {
    some_graph_as_value["optional_integer"] = (*some_graph.optional_integer);
  }

  if (some_graph.optional_map) {
    Json::Value target_1(Json::objectValue);
    const auto& map_1 = (*some_graph.optional_map);
    for (const auto& kv_1 : map_1) {
      target_1[kv_1.first] = kv_1.second;
    }
    some_graph_as_value["optional_map"] = std::move(target_1);
  }

  if (some_graph.optional_path) {
    some_graph_as_value["optional_path"] = (*some_graph.optional_path).string();
  }

  if (some_graph.optional_string) {
    some_graph_as_value["optional_string"] = (*some_graph.optional_string);
  }

  if (some_graph.optional_time) {
    some_graph_as_value["optional_time"] = tm_to_string(
      (*some_graph.optional_time),
      "%H:%M:%S");
  }

  if (some_graph.optional_time_zone) {
    some_graph_as_value["optional_time_zone"] = (*some_graph.optional_time_zone);
  }

  if (some_graph.optional_reference) {
    some_graph_as_value["optional_reference"] = (*some_graph.optional_reference)->id;
  }

  if (some_graph.optional_embed) {
    some_graph_as_value["optional_embed"] = serialize_some_embed((*some_graph.optional_embed));
  }

  if (not some_graph.empties.empty()) {
    Json::Value empties_as_value;
    for (const auto& kv : some_graph.empties) {
      const std::string& id = kv.first;
      const Empty* instance = kv.second.get();

      if (id != instance->id) {
        constexpr auto expected(
          "Expected the class instance of "
          "Empty"
          "to have the ID ");
        constexpr auto but_got(", but got: ");

        std::string msg;
        msg.reserve(
          strlen(expected) + id.size() +
          strlen(but_got) + instance->id.size());
        msg += expected;
        msg += id;
        msg += but_got;
        msg += instance->id;

        throw std::invalid_argument(msg);
      }

      empties_as_value[instance->id] = serialize_empty(*instance);
    }
    some_graph_as_value["empties"] = empties_as_value;
  }

  return some_graph_as_value;
}

}  // namespace jsoncpp

}  // namespace graph
}  // namespace some

// File automatically generated by mapry. DO NOT EDIT OR APPEND!
