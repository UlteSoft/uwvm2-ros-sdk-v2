#include "tinyxml2.h"
#include <cstring>

int main() {
  tinyxml2::XMLDocument original;
  if (original.Parse("<sensor unit='mm'><reading>42</reading></sensor>") != tinyxml2::XML_SUCCESS)
    return 1;
  auto *root = original.RootElement();
  int value = 0;
  auto *reading = root->FirstChildElement("reading");
  if (!reading || reading->QueryIntText(&value) != tinyxml2::XML_SUCCESS || value != 42)
    return 2;
  root->SetAttribute("sample", 7);
  tinyxml2::XMLPrinter printer;
  original.Print(&printer);
  tinyxml2::XMLDocument copy;
  if (copy.Parse(printer.CStr()) != tinyxml2::XML_SUCCESS)
    return 3;
  auto *restored = copy.RootElement();
  if (restored->IntAttribute("sample") != 7 || !restored->Attribute("unit", "mm"))
    return 4;
  return std::strcmp(restored->FirstChildElement("reading")->GetText(), "42") == 0 ? 0 : 5;
}
