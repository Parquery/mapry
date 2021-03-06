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
  // Parse array_of_class_refs
  ////

  if (!value.isMember("array_of_class_refs")) {
    errors->add(
      ref,
      "Property is missing: array_of_class_refs");
  } else {
    const Json::Value& value_0 = value["array_of_class_refs"];
    if (!value_0.isArray()) {
      constexpr auto expected_but_got(
        "Expected an array, but got: ");

      errors->add(
        std::string(ref)
          .append("/array_of_class_refs"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_0.type())));
    } else {
      std::vector<Empty*>& target_0 = target->array_of_class_refs;
      target_0.resize(value_0.size());
      size_t i_0 = 0;
      for (const Json::Value& item_0 : value_0) {
        if (!item_0.isString()) {
          constexpr auto expected_but_got(
            "Expected a string, but got: ");

          errors->add(
            std::string(ref)
              .append("/array_of_class_refs")
              .append("/")
              .append(std::to_string(i_0)),
            message(
              expected_but_got,
              strlen(expected_but_got),
              value_type_to_string(
                item_0.type())));
        } else {
          const std::string& cast_1 = item_0.asString();
          if (target->empties.count(cast_1) == 0) {
            constexpr auto reference_not_found(
              "Reference to an instance of class "
              "Empty"
              " not found: ");

            errors->add(
              std::string(ref)
                .append("/array_of_class_refs")
                .append("/")
                .append(std::to_string(i_0)),
              message(
                reference_not_found,
                strlen(reference_not_found),
                cast_1));
          } else {
            target_0.at(i_0) = target->empties.at(cast_1).get();
          }
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

Json::Value serialize_empty(
    const Empty& empty) {
  return Json::objectValue;
}

Json::Value serialize_some_graph(
    const SomeGraph& some_graph) {
  Json::Value some_graph_as_value;

  Json::Value target_0(Json::arrayValue);
  const auto& vector_0 = some_graph.array_of_class_refs;
  for (int i_0 = 0;
      i_0 < vector_0.size();
      ++i_0) {
    target_0[i_0] = vector_0[i_0]->id;
  }
  some_graph_as_value["array_of_class_refs"] = std::move(target_0);

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
