#pragma once

// File automatically generated by mapry. DO NOT EDIT OR APPEND!

#include <json/json.h>  // jsoncpp

#include <map>
#include <string>

#include "parse.h"
#include "types.h"

namespace some {
namespace graph {

namespace jsoncpp {

/**
 * parses SomeGraph from a JSON value.
 *
 * @param [in] value to be parsed
 * @param [in] ref reference to the value (e.g., a reference path)
 * @param [out] target parsed SomeGraph
 * @param [out] errors encountered during parsing
 */
void some_graph_from(
  const Json::Value& value,
  std::string ref,
  SomeGraph* target,
  parse::Errors* errors);

/**
 * parses SomeClass from a JSON value.
 *
 * @param [in] value to be parsed
 * @param other_classes_registry registry of the OtherClass instances
 * @param some_classes_registry registry of the SomeClass instances
 * @param ref reference to the value (e.g., a reference path)
 * @param [out] target parsed data
 * @param [out] errors encountered during parsing
 */
void some_class_from(
  const Json::Value& value,
  const std::map<std::string, std::unique_ptr<OtherClass>>& other_classes_registry,
  const std::map<std::string, std::unique_ptr<SomeClass>>& some_classes_registry,
  std::string ref,
  SomeClass* target,
  parse::Errors* errors);

/**
 * parses OtherClass from a JSON value.
 *
 * @param [in] value to be parsed
 * @param other_classes_registry registry of the OtherClass instances
 * @param some_classes_registry registry of the SomeClass instances
 * @param ref reference to the value (e.g., a reference path)
 * @param [out] target parsed data
 * @param [out] errors encountered during parsing
 */
void other_class_from(
  const Json::Value& value,
  const std::map<std::string, std::unique_ptr<OtherClass>>& other_classes_registry,
  const std::map<std::string, std::unique_ptr<SomeClass>>& some_classes_registry,
  std::string ref,
  OtherClass* target,
  parse::Errors* errors);


/**
 * serializes SomeGraph to a JSON value.
 *
 * @param some_graph to be serialized
 * @return JSON value
 */
Json::Value serialize_some_graph(
  const SomeGraph& some_graph);

/**
 * serializes SomeClass to a JSON value.
 *
 * @param some_class to be serialized
 * @return JSON value
 */
Json::Value serialize_some_class(
  const SomeClass& some_class);

/**
 * serializes OtherClass to a JSON value.
 *
 * @param other_class to be serialized
 * @return JSON value
 */
Json::Value serialize_other_class(
  const OtherClass& other_class);

}  // namespace jsoncpp

}  // namespace graph
}  // namespace some

// File automatically generated by mapry. DO NOT EDIT OR APPEND!
