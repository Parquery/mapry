#include <functional>
#include <iostream>
#include <memory>
#include <string>

struct A;
struct B;

struct B {
  std::string identifier;
  const A& a;

  B(std::string&& an_identifier,
    const A& an_a) :
      identifier(an_identifier),
      a(an_a) {}
};

struct A {
  std::string identifier;
  const B& b;

  A(std::string&& an_identifier,
    const B& a_b) :
      identifier(an_identifier),
      b(a_b) {}
};

int main() {
  // pre-allocate memory for an instance of A
  std::unique_ptr<A> a_ptr(
      reinterpret_cast<A*>(
          ::operator new(sizeof(A))));

  // pre-allocate memory for an instance of B
  std::unique_ptr<B> b_ptr(
      reinterpret_cast<B*>(
          ::operator new(sizeof(B))));

  // construct a and b
  new (a_ptr.get()) A("some a", *b_ptr);
  new (b_ptr.get()) B("some b", *a_ptr);

  std::cout << "a->b.identifier: " << a_ptr->b.identifier << std::endl;
  std::cout << "b->a.identifier: " << b_ptr->a.identifier << std::endl;
}
