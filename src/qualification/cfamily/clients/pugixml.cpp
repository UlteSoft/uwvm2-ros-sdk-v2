#include "pugixml.hpp"
#include <cstring>

int main() {
  pugi::xml_document doc;
  if (!doc.load_string("<r><item k='a'>3</item><item k='b'>13</item></r>"))
    return 1;
  auto nodes = doc.select_nodes("/r/item[@k='b']");
  if (nodes.size() != 1 || nodes.first().node().text().as_int() != 13)
    return 2;
  auto root = doc.document_element();
  auto copy = root.append_copy(nodes.first().node());
  if (!copy.attribute("k").set_value("copy") || !copy.text().set(21))
    return 3;
  if (root.first_child().text().as_int() != 3 ||
      std::strcmp(root.last_child().attribute("k").value(), "copy") != 0)
    return 4;
  return doc.select_node("/r/item[@k='copy']").node().text().as_int() == 21 ? 0 : 5;
}
