#include <array>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include <fastcdr/Cdr.h>
#include <fastcdr/FastBuffer.h>

using namespace eprosima::fastcdr;

struct Operation {
    std::string type;
    std::string text;
};

template<class T>
void transfer(Cdr& cdr, T expected, bool read) {
    if (read) {
        T value{};
        cdr >> value;
        if (value != expected) throw std::runtime_error("Fast-CDR readback differs");
    } else {
        cdr << expected;
    }
}

void apply(Cdr& cdr, const std::vector<Operation>& operations, bool read) {
    for (const auto& op : operations) {
        if (op.type == "bool")        transfer(cdr, op.text == "1", read);
        else if (op.type == "uint8")  transfer(cdr, static_cast<uint8_t>(std::stoul(op.text)), read);
        else if (op.type == "int8")   transfer(cdr, static_cast<int8_t>(std::stol(op.text)), read);
        else if (op.type == "uint32") transfer(cdr, static_cast<uint32_t>(std::stoul(op.text)), read);
        else if (op.type == "int32")  transfer(cdr, static_cast<int32_t>(std::stol(op.text)), read);
        else if (op.type == "int64")  transfer(cdr, static_cast<int64_t>(std::stoll(op.text)), read);
        else if (op.type == "float64") transfer(cdr, std::stod(op.text), read);
        else if (op.type == "string") transfer(cdr, op.text, read);
        else throw std::runtime_error("Unsupported oracle operand " + op.type);
    }
}

int main() {
    std::ifstream input("plans.tsv");
    if (!input) throw std::runtime_error("Cannot open oracle plan");
    std::vector<Operation> operations;
    std::string label;
    std::string line;
    size_t frames = 0;
    while (std::getline(input, line)) {
        if (line.empty()) {
            if (operations.empty()) throw std::runtime_error("Empty oracle operation list");
            for (const auto endian : {Cdr::LITTLE_ENDIANNESS, Cdr::BIG_ENDIANNESS}) {
                std::array<char, 16384> bytes{};
                FastBuffer write_buffer(bytes.data(), bytes.size());
                Cdr writer(write_buffer, endian, CdrVersion::XCDRv1);
                writer.set_encoding_flag(EncodingAlgorithmFlag::PLAIN_CDR);
                writer.serialize_encapsulation();
                apply(writer, operations, false);
                writer.set_dds_cdr_options({0, 0});
                const auto length = writer.get_serialized_data_length();
                FastBuffer read_buffer(bytes.data(), length);
                Cdr reader(read_buffer, Cdr::DEFAULT_ENDIAN, CdrVersion::XCDRv1);
                reader.read_encapsulation();
                apply(reader, operations, true);
                if (reader.get_serialized_data_length() != length) throw std::runtime_error("Incomplete Fast-CDR readback");
                const auto order = endian == Cdr::LITTLE_ENDIANNESS ? "-le.cdr" : "-be.cdr";
                std::ofstream out("vectors/" + label + order, std::ios::binary);
                out.write(bytes.data(), length);
                if (!out) throw std::runtime_error("Cannot write oracle");
                ++frames;
            }
            operations.clear();
            label.clear();
        } else if (label.empty()) {
            label = line;
        } else {
            const auto tab = line.find('\t');
            if (tab == std::string::npos) throw std::runtime_error("Invalid oracle operation");
            operations.push_back({line.substr(0, tab), line.substr(tab + 1)});
        }
    }
    if (!label.empty() || !frames) throw std::runtime_error("Missing oracle record terminator");
    std::cout << frames << " independent Fast-CDR 2.2.5 XCDRv1 PLAIN_CDR frames serialized and read back\n";
}
