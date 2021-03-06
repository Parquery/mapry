#pragma once

// File automatically generated by mapry. DO NOT EDIT OR APPEND!

#include <date/date.h>

#include <chrono>

namespace some {
namespace graph {

struct SomeGraph;

// defines some object graph.
struct SomeGraph {
  // defines some time.
  date::time_of_day<std::chrono::seconds> some_time;

  // defines some formatless time.
  date::time_of_day<std::chrono::seconds> formatless_time;
};

}  // namespace graph
}  // namespace some

// File automatically generated by mapry. DO NOT EDIT OR APPEND!
