#include <json/json.h>

#include <iostream>
#include <string>
#include <sstream>

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
      ss << "Unhandled value type: " << value_type;
      throw std::domain_error(ss.str());
  }
}

void play_with_arrays() {
  std::cout << "Playing with arrays..." << std::endl;

  std::stringstream ss;
  ss << "[4,3,2]";

  Json::Value root;
  ss >> root;

  std::cout << "root is: " << root << std::endl;
  std::cout << "root is array: " << root.isArray() << std::endl;
  std::cout << "root is object: " << root.isObject() << std::endl;
  std::cout << "root type: " << value_type_to_string(root.type()) << std::endl;
}

void play_with_objects() {
  std::cout << "Playing with objects..." << std::endl;

  std::stringstream ss;
  ss << R"({"x": 3, "y": "oi"})";

  Json::Value root;
  ss >> root;

  std::cout << "root is: " << root << std::endl;
  std::cout << "root is array: " << root.isArray() << std::endl;
  std::cout << "root is object: " << root.isObject() << std::endl;
  std::cout << "root.isMember(x): " << root.isMember("x") << std::endl;
  std::cout << "root.isMember(z): " << root.isMember("z") << std::endl;
  std::cout << "root type: " << value_type_to_string(root.type()) << std::endl;


  // iterate over keys and values

  for (Json::ValueConstIterator it = root.begin(); it != root.end(); ++it) {
    std::cout << "key is: " << it.key() << std::endl;
    std::cout << "value is: " << *it << std::endl;
  }
}

int main() {
  play_with_arrays();
  play_with_objects();

  return 0;
}