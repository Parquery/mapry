#pragma once

// File automatically generated by mapry. DO NOT EDIT OR APPEND!

#include <boost/optional.hpp>
#include <json/json.h>  // jsoncpp



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
 * serializes SomeGraph to a JSON value.
 *
 * @param some_graph to be serialized
 * @return JSON value
 */
Json::Value serialize_some_graph(
  const SomeGraph& some_graph);

}  // namespace jsoncpp

}  // namespace graph
}  // namespace some

// File automatically generated by mapry. DO NOT EDIT OR APPEND!
