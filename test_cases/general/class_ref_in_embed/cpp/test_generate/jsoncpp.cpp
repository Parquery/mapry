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
  // Pre-allocate empties
  ////

  std::string empties_ref;
  empties_ref.reserve(ref.size() + 8);
  empties_ref += ref;
  empties_ref += "/empties";

  if (value.isMember("empties")) {
    const Json::Value& obj = value["empties"];
    if (!obj.isObject()) {
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
  if (!errors->empty()) {
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
  // Parse some_embed
  ////

  if (!value.isMember("some_embed")) {
    errors->add(
      ref,
      "Property is missing: some_embed");
  } else {
    const Json::Value& value_0 = value["some_embed"];
    embed_with_ref_from(
      value_0,
      target->empties,
      std::string(ref)
        .append("/some_embed"),
      &target->some_embed,
      errors);
  }
  if (errors->full()) {
    return;
  }
}

void empty_from(
    const Json::Value& value,
    std::string ref,
    Empty* target,
    parse::Errors* errors) {
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
}

void embed_with_ref_from(
    const Json::Value& value,
    const std::map<std::string, std::unique_ptr<Empty>>& empties_registry,
    std::string ref,
    EmbedWithRef* target,
    parse::Errors* errors) {
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
  // Parse reference_to_empty
  ////

  if (!value.isMember("reference_to_empty")) {
    errors->add(
      ref,
      "Property is missing: reference_to_empty");
  } else {
    const Json::Value& value_0 = value["reference_to_empty"];
    if (!value_0.isString()) {
      constexpr auto expected_but_got(
        "Expected a string, but got: ");

      errors->add(
        std::string(ref)
          .append("/reference_to_empty"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_0.type())));
    } else {
      const std::string& cast_0 = value_0.asString();
      if (empties_registry.count(cast_0) == 0) {
        constexpr auto reference_not_found(
          "Reference to an instance of class "
          "Empty"
          " not found: ");

        errors->add(
          std::string(ref)
            .append("/reference_to_empty"),
          message(
            reference_not_found,
            strlen(reference_not_found),
            cast_0));
      } else {
        target->reference_to_empty = empties_registry.at(cast_0).get();
      }
    }
  }
  if (errors->full()) {
    return;
  }
}

Json::Value serialize_empty(
    const Empty& empty) {
  return Json::objectValue;
}

Json::Value serialize_embed_with_ref(
    const EmbedWithRef& embed_with_ref) {
  Json::Value embed_with_ref_as_value;

  embed_with_ref_as_value["reference_to_empty"] = embed_with_ref.reference_to_empty->id;

  return embed_with_ref_as_value;
}

Json::Value serialize_some_graph(
    const SomeGraph& some_graph) {
  Json::Value some_graph_as_value;

  some_graph_as_value["some_embed"] = serialize_embed_with_ref(some_graph.some_embed);

  if (!some_graph.empties.empty()) {
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
