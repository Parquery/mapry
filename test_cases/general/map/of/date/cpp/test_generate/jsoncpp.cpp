// File automatically generated by mapry. DO NOT EDIT OR APPEND!

#include "jsoncpp.h"
#include "parse.h"
#include "types.h"

#include <cstring>
#include <memory>
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

  if (!errors->empty()) {
    throw std::invalid_argument("Unexpected non-empty errors");
  }

  if (!value.isObject()) {
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
  // Parse map_of_dates
  ////

  if (!value.isMember("map_of_dates")) {
    errors->add(
      ref,
      "Property is missing: map_of_dates");
  } else {
    const Json::Value& value_0 = value["map_of_dates"];
    if (!value_0.isObject()) {
      constexpr auto expected_but_got(
        "Expected an object, but got: ");

      errors->add(
        std::string(ref)
          .append("/map_of_dates"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_0.type())));
    } else {
      std::map<std::string, struct tm>& target_0 = target->map_of_dates;
      for (Json::ValueConstIterator it_0 = value_0.begin(); it_0 != value_0.end(); ++it_0) {
        const Json::Value& value_1 = *it_0;
        if (!value_1.isString()) {
          constexpr auto expected_but_got(
            "Expected a string, but got: ");

          errors->add(
            std::string(ref)
              .append("/map_of_dates")
              .append("/")
              .append(it_0.name()),
            message(
              expected_but_got,
              strlen(expected_but_got),
              value_type_to_string(
                value_1.type())));
        } else {
          const std::string cast_1 = value_1.asString();
          struct tm tm_1 = tm{0};
          char* ret_1 = strptime(
            cast_1.c_str(),
            "%Y-%m-%d",
            &tm_1);

          if (ret_1 == nullptr or *ret_1 != '\0') {
            constexpr auto expected_but_got(
              "Expected to strptime "
              "%Y-%m-%d"
              ", but got: ");

            errors->add(
              std::string(ref)
                .append("/map_of_dates")
                .append("/")
                .append(it_0.name()),
              message(
                expected_but_got,
                strlen(expected_but_got),
                cast_1));
          } else {
            target_0[it_0.name()] = tm_1;
          }
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

Json::Value serialize_some_graph(
    const SomeGraph& some_graph) {
  Json::Value some_graph_as_value;

  Json::Value target_0(Json::objectValue);
  const auto& map_0 = some_graph.map_of_dates;
  for (const auto& kv_0 : map_0) {
    target_0[kv_0.first] = tm_to_string(
      kv_0.second,
      "%Y-%m-%d");
  }
  some_graph_as_value["map_of_dates"] = std::move(target_0);

  return some_graph_as_value;
}

}  // namespace jsoncpp

}  // namespace graph
}  // namespace some

// File automatically generated by mapry. DO NOT EDIT OR APPEND!
