// File automatically generated by mapry. DO NOT EDIT OR APPEND!

#include "jsoncpp.h"
#include "parse.h"
#include "types.h"

#include <cstring>
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

namespace empty_re {
const std::regex kID(
  R"v0g0n(^[a-zA-Z_\-][a-zA-Z_0-9\-]*$)v0g0n");
}  // namespace empty_re

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
        if (!std::regex_match(
            it.name(),
            empty_re::kID)) {
          constexpr auto expected_but_got(
            "Expected ID to match "
            "^[a-zA-Z_\\-][a-zA-Z_0-9\\-]*$"
            ", but got: ");

          errors->add(
            empties_ref,
            message(
              expected_but_got,
              strlen(expected_but_got),
              it.name()));

          if (errors->full()) {
            break;
          }
        } else {
                  auto instance = std::make_unique<Empty>();
          instance->id = it.name();
          target->empties[it.name()] = std::move(instance);

        }
      }
    }
  }

  ////
  // Pre-allocate with_references
  ////

  std::string with_references_ref;
  with_references_ref.reserve(ref.size() + 16);
  with_references_ref += ref;
  with_references_ref += "/with_references";

  if (value.isMember("with_references")) {
    const Json::Value& obj = value["with_references"];
    if (!obj.isObject()) {
      constexpr auto expected_but_got(
        "Expected an object, but got: ");

      errors->add(
        with_references_ref,
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            obj.type())));
    } else {
      for (Json::ValueConstIterator it = obj.begin();
          it != obj.end(); ++it) {
                auto instance = std::make_unique<WithReference>();
        instance->id = it.name();
        target->with_references[it.name()] = std::move(instance);

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
  // Parse with_references
  ////

  // clear() does not shrink the reserved memory,
  // see https://en.cppreference.com/w/cpp/string/basic_string/clear
  instance_ref.clear();
  instance_ref += with_references_ref;
  instance_ref += '/';

  if (value.isMember("with_references")) {
    const Json::Value& obj = value["with_references"];

    for (Json::ValueConstIterator it = obj.begin(); it != obj.end(); ++it) {
      instance_ref.reserve(
        with_references_ref.size() + 1 + it.name().size());
      instance_ref.resize(
        with_references_ref.size() + 1);
      instance_ref.append(
        it.name());

      WithReference* instance(
        target->with_references.at(it.name()).get());
      with_reference_from(
        *it,
        target->empties,
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
  // Parse global_reference_to_an_empty
  ////

  if (!value.isMember("global_reference_to_an_empty")) {
    errors->add(
      ref,
      "Property is missing: global_reference_to_an_empty");
  } else {
    const Json::Value& value_0 = value["global_reference_to_an_empty"];
    if (!value_0.isString()) {
      constexpr auto expected_but_got(
        "Expected a string, but got: ");

      errors->add(
        std::string(ref)
          .append("/global_reference_to_an_empty"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_0.type())));
    } else {
      const std::string& cast_0 = value_0.asString();
      if (target->empties.count(cast_0) == 0) {
        constexpr auto reference_not_found(
          "Reference to an instance of class "
          "Empty"
          " not found: ");

        errors->add(
          std::string(ref)
            .append("/global_reference_to_an_empty"),
          message(
            reference_not_found,
            strlen(reference_not_found),
            cast_0));
      } else {
        target->global_reference_to_an_empty = target->empties.at(cast_0).get();
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

void with_reference_from(
    const Json::Value& value,
    const std::map<std::string, std::unique_ptr<Empty>>& empties_registry,
    std::string ref,
    WithReference* target,
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
  // Parse reference_to_an_empty
  ////

  if (!value.isMember("reference_to_an_empty")) {
    errors->add(
      ref,
      "Property is missing: reference_to_an_empty");
  } else {
    const Json::Value& value_0 = value["reference_to_an_empty"];
    if (!value_0.isString()) {
      constexpr auto expected_but_got(
        "Expected a string, but got: ");

      errors->add(
        std::string(ref)
          .append("/reference_to_an_empty"),
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
            .append("/reference_to_an_empty"),
          message(
            reference_not_found,
            strlen(reference_not_found),
            cast_0));
      } else {
        target->reference_to_an_empty = empties_registry.at(cast_0).get();
      }
    }
  }
  if (errors->full()) {
    return;
  }

  ////
  // Parse array_of_empties
  ////

  if (!value.isMember("array_of_empties")) {
    errors->add(
      ref,
      "Property is missing: array_of_empties");
  } else {
    const Json::Value& value_1 = value["array_of_empties"];
    if (!value_1.isArray()) {
      constexpr auto expected_but_got(
        "Expected an array, but got: ");

      errors->add(
        std::string(ref)
          .append("/array_of_empties"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_1.type())));
    } else {
      std::vector<Empty*>& target_1 = target->array_of_empties;
      target_1.resize(value_1.size());
      size_t i_1 = 0;
      for (const Json::Value& item_1 : value_1) {
        if (!item_1.isString()) {
          constexpr auto expected_but_got(
            "Expected a string, but got: ");

          errors->add(
            std::string(ref)
              .append("/array_of_empties")
              .append("/")
              .append(std::to_string(i_1)),
            message(
              expected_but_got,
              strlen(expected_but_got),
              value_type_to_string(
                item_1.type())));
        } else {
          const std::string& cast_2 = item_1.asString();
          if (empties_registry.count(cast_2) == 0) {
            constexpr auto reference_not_found(
              "Reference to an instance of class "
              "Empty"
              " not found: ");

            errors->add(
              std::string(ref)
                .append("/array_of_empties")
                .append("/")
                .append(std::to_string(i_1)),
              message(
                reference_not_found,
                strlen(reference_not_found),
                cast_2));
          } else {
            target_1.at(i_1) = empties_registry.at(cast_2).get();
          }
        }
        ++i_1;

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
  // Parse map_of_empties
  ////

  if (!value.isMember("map_of_empties")) {
    errors->add(
      ref,
      "Property is missing: map_of_empties");
  } else {
    const Json::Value& value_3 = value["map_of_empties"];
    if (!value_3.isObject()) {
      constexpr auto expected_but_got(
        "Expected an object, but got: ");

      errors->add(
        std::string(ref)
          .append("/map_of_empties"),
        message(
          expected_but_got,
          strlen(expected_but_got),
          value_type_to_string(
            value_3.type())));
    } else {
      std::map<std::string, Empty*>& target_3 = target->map_of_empties;
      for (Json::ValueConstIterator it_3 = value_3.begin(); it_3 != value_3.end(); ++it_3) {
        const Json::Value& value_4 = *it_3;
        if (!value_4.isString()) {
          constexpr auto expected_but_got(
            "Expected a string, but got: ");

          errors->add(
            std::string(ref)
              .append("/map_of_empties")
              .append("/")
              .append(it_3.name()),
            message(
              expected_but_got,
              strlen(expected_but_got),
              value_type_to_string(
                value_4.type())));
        } else {
          const std::string& cast_4 = value_4.asString();
          if (empties_registry.count(cast_4) == 0) {
            constexpr auto reference_not_found(
              "Reference to an instance of class "
              "Empty"
              " not found: ");

            errors->add(
              std::string(ref)
                .append("/map_of_empties")
                .append("/")
                .append(it_3.name()),
              message(
                reference_not_found,
                strlen(reference_not_found),
                cast_4));
          } else {
            target_3[it_3.name()] = empties_registry.at(cast_4).get();
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

Json::Value serialize_empty(
    const Empty& empty) {
  return Json::objectValue;
}

Json::Value serialize_with_reference(
    const WithReference& with_reference) {
  Json::Value with_reference_as_value;

  with_reference_as_value["reference_to_an_empty"] = with_reference.reference_to_an_empty->id;

  Json::Value target_0(Json::arrayValue);
  const auto& vector_0 = with_reference.array_of_empties;
  for (int i_0 = 0;
      i_0 < vector_0.size();
      ++i_0) {
    target_0[i_0] = vector_0[i_0]->id;
  }
  with_reference_as_value["array_of_empties"] = std::move(target_0);

  Json::Value target_1(Json::objectValue);
  const auto& map_1 = with_reference.map_of_empties;
  for (const auto& kv_1 : map_1) {
    target_1[kv_1.first] = kv_1.second->id;
  }
  with_reference_as_value["map_of_empties"] = std::move(target_1);

  return with_reference_as_value;
}

Json::Value serialize_some_graph(
    const SomeGraph& some_graph) {
  Json::Value some_graph_as_value;

  some_graph_as_value["global_reference_to_an_empty"] = some_graph.global_reference_to_an_empty->id;

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

  if (!some_graph.with_references.empty()) {
    Json::Value with_references_as_value;
    for (const auto& kv : some_graph.with_references) {
      const std::string& id = kv.first;
      const WithReference* instance = kv.second.get();

      if (id != instance->id) {
        constexpr auto expected(
          "Expected the class instance of "
          "WithReference"
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

      with_references_as_value[instance->id] = serialize_with_reference(*instance);
    }
    some_graph_as_value["with_references"] = with_references_as_value;
  }

  return some_graph_as_value;
}

}  // namespace jsoncpp

}  // namespace graph
}  // namespace some

// File automatically generated by mapry. DO NOT EDIT OR APPEND!
