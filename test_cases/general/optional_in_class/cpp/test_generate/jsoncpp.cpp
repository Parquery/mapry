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
  // Pre-allocate with_optionals
  ////

  std::string with_optionals_ref;
  with_optionals_ref.reserve(ref.size() + 15);
  with_optionals_ref += ref;
  with_optionals_ref += "/with_optionals";

  if (value.isMember("with_optionals")) {
    const Json::Value& obj = value["with_optionals"];
    if (not obj.isObject()) {
      constexpr auto expected_but_got(
        "Expected an object, but got: ");

      errors->add(
        with_optionals_ref,
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            obj.type())));
    } else {
      for (Json::ValueConstIterator it = obj.begin();
          it != obj.end(); ++it) {
                auto instance = std::make_unique<WithOptional>();
        instance->id = it.name();
        target->with_optionals[it.name()] = std::move(instance);

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
  // Parse with_optionals
  ////

  // clear() does not shrink the reserved memory,
  // see https://en.cppreference.com/w/cpp/string/basic_string/clear
  instance_ref.clear();
  instance_ref += with_optionals_ref;
  instance_ref += '/';

  if (value.isMember("with_optionals")) {
    const Json::Value& obj = value["with_optionals"];

    for (Json::ValueConstIterator it = obj.begin(); it != obj.end(); ++it) {
      instance_ref.reserve(
        with_optionals_ref.size() + 1 + it.name().size());
      instance_ref.resize(
        with_optionals_ref.size() + 1);
      instance_ref.append(
        it.name());

      WithOptional* instance(
        target->with_optionals.at(it.name()).get());
      with_optional_from(
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
}

void with_optional_from(
    const Json::Value& value,
    std::string ref,
    WithOptional* target,
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

  ////
  // Parse some_text
  ////

  if (value.isMember("some_text")) {
    const Json::Value& value_0 = value["some_text"];
    if (not value_0.isString()) {
      constexpr auto expected_but_got(
        "Expected a string, but got: ");

      errors->add(
        std::string(ref)
          .append("/some_text"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_0.type())));
    } else {
      target->some_text = value_0.asString();
    }
  }
  if (errors->full()) {
    return;
  }
}

Json::Value serialize_with_optional(
    const WithOptional& with_optional) {
  Json::Value with_optional_as_value;

  if (with_optional.some_text) {
    with_optional_as_value["some_text"] = (*with_optional.some_text);
  }

  return with_optional_as_value;
}

Json::Value serialize_some_graph(
    const SomeGraph& some_graph) {
  Json::Value some_graph_as_value;

  if (not some_graph.with_optionals.empty()) {
    Json::Value with_optionals_as_value;
    for (const auto& kv : some_graph.with_optionals) {
      const std::string& id = kv.first;
      const WithOptional* instance = kv.second.get();

      if (id != instance->id) {
        constexpr auto expected(
          "Expected the class instance of "
          "WithOptional"
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

      with_optionals_as_value[instance->id] = serialize_with_optional(*instance);
    }
    some_graph_as_value["with_optionals"] = with_optionals_as_value;
  }

  return some_graph_as_value;
}

}  // namespace jsoncpp

}  // namespace graph
}  // namespace some

// File automatically generated by mapry. DO NOT EDIT OR APPEND!